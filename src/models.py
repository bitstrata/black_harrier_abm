from __future__ import annotations

import random
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector
from scipy.spatial import cKDTree as KDTree

from src.config import (
    BSA_HEIGHT,
    MIGRATION_HEIGHT,
    BREEDING_MONTHS,
    MIGRATION_MONTHS,
    FORAGING_RANGE,
    NON_BREEDING_RANGE,
    DISPLACEMENT_RADIUS,
    NEST_FAIL_PROB,
    ROOST_BUFFER_COMMUNAL,
    ROOST_BUFFER_SINGLE,
    NEST_BUFFER_VERY_HIGH,
    MITIGATION_BLADE_PAINT,
    MITIGATION_SHUTDOWN,
    PREY_REDUCTION_FACTOR,
    AVOIDANCE_RATE_PRIOR,
    COLLISION_PROB_PRIOR,
)
from src.bayesian_utils import bayesian_update_collision_prob
from src.data_processing import (
    process_gps_data,
    process_lidar_data,
    process_weather_data,
    process_turbine_data,
    build_graph,
    Point,
)

# -----------------------------
# Utility helpers (vectorized)
# -----------------------------
def _any_within_radius(points: np.ndarray, center: np.ndarray, radius: float) -> bool:
    if points.size == 0:
        return False
    diffs = points - center
    return np.any(np.einsum("ij,ij->i", diffs, diffs) < radius * radius)

def _nearest_index_kdtree(tree: Optional[KDTree], node_positions: np.ndarray, pos: Tuple[float, float]) -> int:
    if tree is None or len(node_positions) == 0:
        return 0
    _, idx = tree.query(pos)
    return int(idx)

# -----------------------------
# Harrier Agent
# -----------------------------
class HarrierAgent(Agent):
    def __init__(self, unique_id: int, model: "HarrierModel", pos: Tuple[float, float], breeding: bool = False):
        super().__init__(unique_id, model)
        self.pos: Tuple[float, float] = pos
        self.height: float = random.uniform(0, 100)
        self.breeding: bool = breeding
        self.alive: bool = True
        self.nest: Optional[Tuple[float, float]] = random.choice(self.model.nests) if breeding and self.model.nests else None
        self.breeding_month: Optional[int] = random.choice(BREEDING_MONTHS) if breeding else None
        self.energy: float = 100.0
        self.current_node: Optional[int] = None

    def _set_flight_profile(self, month: int) -> float:
        if month in BREEDING_MONTHS and self.breeding:
            self.height = random.uniform(BSA_HEIGHT[0], BSA_HEIGHT[1]) if random.random() < 0.35 else random.uniform(0, 30)
            return FORAGING_RANGE
        elif month in MIGRATION_MONTHS:
            self.height = random.uniform(MIGRATION_HEIGHT[0], MIGRATION_HEIGHT[1])
            return NON_BREEDING_RANGE
        else:
            self.height = random.uniform(0, 30)
            return NON_BREEDING_RANGE

    def move(self) -> None:
        if not self.alive:
            return

        month = self.model.month
        G = self.model.graph

        if self.current_node is None:
            self.current_node = _nearest_index_kdtree(self.model._graph_kdtree, self.model._node_positions, self.pos)

        _ = self._set_flight_profile(month)

        neighbors = list(G.neighbors(self.current_node))
        if not neighbors:
            return

        weights: List[float] = []
        for n in neighbors:
            prob = self.model.transition_probs.get((month, self.current_node, n), 1.0 / len(neighbors))
            edge = G[self.current_node][n]
            thermal = edge.get("thermal", 1.0)

            # Wake-loss: reduce thermal near turbines (isotropic, exponential decay)
            if self.model.wake_loss:
                p0 = np.array(G.nodes[self.current_node]["pos"], dtype=float)
                p1 = np.array(G.nodes[n]["pos"], dtype=float)
                midpoint = 0.5 * (p0 + p1)
                thermal *= self.model._wake_multiplier(midpoint)

            risk = edge.get("turbine_risk", 0.0) if edge.get("turbine_active", False) else 0.0
            weights.append(prob * thermal / (1.0 + risk))

        next_node = random.choices(neighbors, weights=weights, k=1)[0]
        new_pos = G.nodes[next_node]["pos"]

        if _any_within_radius(self.model._turbine_positions, np.array(new_pos), DISPLACEMENT_RADIUS):
            return

        self.pos = tuple(new_pos)
        self.current_node = next_node
        self.energy -= 1.0

    def check_collision(self) -> bool:
        if not self.alive:
            return False

        month = self.model.month
        within_bsa = month in BREEDING_MONTHS and (BSA_HEIGHT[0] <= self.height <= BSA_HEIGHT[1])
        within_migration = month in MIGRATION_MONTHS and (MIGRATION_HEIGHT[0] <= self.height <= MIGRATION_HEIGHT[1])
        if not (within_bsa or within_migration):
            return False

        pos_arr = np.array(self.pos)

        if not _any_within_radius(self.model._turbine_positions, pos_arr, 1.0):
            return False

        if _any_within_radius(self.model._nest_positions, pos_arr, NEST_BUFFER_VERY_HIGH):
            return False
        if _any_within_radius(self.model._communal_roost_positions, pos_arr, ROOST_BUFFER_COMMUNAL):
            return False
        if _any_within_radius(self.model._single_roost_positions, pos_arr, ROOST_BUFFER_SINGLE):
            return False

        if random.random() <= self.model.avoidance_rate:
            return False

        collision_prob = self.model.collision_prob
        if random.random() < MITIGATION_BLADE_PAINT:
            collision_prob *= (1.0 - 0.71)
        if random.random() < MITIGATION_SHUTDOWN and month in BREEDING_MONTHS:
            collision_prob *= (1.0 - 0.50)
        if random.random() < PREY_REDUCTION_FACTOR:
            collision_prob *= (1.0 - 0.50)

        if random.random() < collision_prob:
            self.alive = False
            return True
        return False

    def breed(self) -> int:
        if not (self.alive and self.breeding and (self.model.month in BREEDING_MONTHS)):
            return 0
        if random.random() < NEST_FAIL_PROB and (self.unique_id % 2 == 0):
            return 0
        return 2 if random.random() < 0.7 else 0

# -----------------------------
# ABM Model (refactored with optional wake-loss & configurable replacement policy)
# -----------------------------
class HarrierModel(Model):
    def __init__(self, gps_file: str, lidar_file: str, weather_file: str, turbine_file: str,
                 *, wake_loss: bool = False, wake_coeff: float = 0.15, wake_decay: float = 2.0,
                 replacement_policy: str = "immediate"):
        super().__init__()

        self.schedule = RandomActivation(self)
        self.space = ContinuousSpace(100, 100, torus=False)

        self.month: int = 1
        self._last_month: int = self.month

        # Data loading
        waypoints, agents_df, self.transition_probs = process_gps_data(gps_file)
        nodes = process_lidar_data(lidar_file)
        thermal_data = process_weather_data(weather_file)
        turbines_df = process_turbine_data(turbine_file)

        self.graph = build_graph(waypoints, nodes, turbines_df, thermal_data)

        self._node_positions = np.array([self.graph.nodes[n]["pos"] for n in self.graph.nodes])
        self._graph_kdtree: Optional[KDTree] = KDTree(self._node_positions) if len(self._node_positions) else None

        self.turbines: List[Tuple[float, float]] = [(row["lon"], row["lat"]) for _, row in turbines_df.iterrows()] if len(turbines_df) else []
        self._turbine_positions = np.array(self.turbines, dtype=float) if self.turbines else np.empty((0, 2), dtype=float)
        self._turbine_kdtree: Optional[KDTree] = KDTree(self._turbine_positions) if self._turbine_positions.size else None

        # Example nests/roosts (ideally from data)
        self.nests: List[Tuple[float, float]] = [(random.uniform(20, 80), random.uniform(20, 80)) for _ in range(5)]
        self.communal_roosts: List[Tuple[float, float]] = [(50.0, 50.0)]
        self.single_roosts: List[Tuple[float, float]] = [(random.uniform(0, 99), random.uniform(0, 99)) for _ in range(10)]

        self._nest_positions = np.array(self.nests, dtype=float) if self.nests else np.empty((0, 2), dtype=float)
        self._communal_roost_positions = np.array(self.communal_roosts, dtype=float) if self.communal_roosts else np.empty((0, 2), dtype=float)
        self._single_roost_positions = np.array(self.single_roosts, dtype=float) if self.single_roosts else np.empty((0, 2), dtype=float)

        self.avoidance_rate: float = AVOIDANCE_RATE_PRIOR
        self.collision_prob: float = COLLISION_PROB_PRIOR

        # Wake & replacement policy
        self.wake_loss: bool = bool(wake_loss)
        self.wake_coeff: float = float(wake_coeff)
        self.wake_decay: float = float(wake_decay)
        self.replacement_policy: str = replacement_policy  # 'immediate' or 'seasonal'
        self.pending_recruits: int = 0

        self._init_agents(agents_df)

        self.datacollector = DataCollector(
            model_reporters={
                "Population": lambda m: sum(1 for a in m.schedule.agents if getattr(a, "alive", False)),
                "Fatalities": lambda m: m.fatalities,
                "Fledglings": lambda m: m.fledglings,
                "Collision_Prob": lambda m: m.collision_prob,
            },
            agent_reporters={
                "Position": lambda a: getattr(a, "pos", (None, None)),
                "Height": lambda a: getattr(a, "height", None),
                "Alive": lambda a: getattr(a, "alive", False),
            },
        )

        self.fatalities: int = 0
        self.fledglings: int = 0
        self.curtailment_schedule: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(len(self.turbines))}

        self.gps_data = pd.read_csv(gps_file)
        self._turbines_df_cached = turbines_df

    def _init_agents(self, agents_df: pd.DataFrame) -> None:
        n_agents = len(agents_df)
        breeding_cut = int(0.12 * n_agents)
        for i, row in agents_df.iterrows():
            init_pt = row["initial_pos"]
            pos = (init_pt.x, init_pt.y)
            breeding = bool(row.get("breeding", i < breeding_cut))
            agent = HarrierAgent(int(i), self, pos, breeding)
            self.schedule.add(agent)
            self.space.place_agent(agent, pos)

    def step(self) -> None:
        self.month = (self.month % 12) + 1
        self.fatalities = 0
        self.fledglings = 0

        self.collision_prob = bayesian_update_collision_prob(
            self.collision_prob, self.gps_data, self._turbines_df_cached
        )

        for agent in list(self.schedule.agents):
            agent.move()
            if agent.check_collision():
                self.fatalities += 1
                if self._turbine_positions.size:
                    if self._turbine_kdtree is not None:
                        _, tid = self._turbine_kdtree.query(np.array(agent.pos))
                        tid = int(tid)
                    else:
                        diffs = self._turbine_positions - np.array(agent.pos)
                        tid = int(np.argmin(np.einsum("ij,ij->i", diffs, diffs)))
                    hour = self.schedule.steps % 24
                    self.curtailment_schedule[tid].append((self.month, hour))
            self.fledglings += agent.breed()

        # Remove dead agents (safe ID reuse)
        dead_agents = [a for a in self.schedule.agents if not getattr(a, "alive", True)]
        for agent in dead_agents:
            try:
                self.space.remove_agent(agent)
            except Exception:
                pass
            try:
                self.schedule.remove(agent)
            except Exception:
                pass

        if self.replacement_policy == "immediate":
            # Replace now, bounded by fledglings
            for agent in dead_agents:
                if self.fledglings <= 0:
                    break
                new_pos = (random.uniform(0, 99), random.uniform(0, 99))
                new_agent = HarrierAgent(agent.unique_id, self, new_pos, agent.breeding)
                self.schedule.add(new_agent)
                self.space.place_agent(new_agent, new_pos)
                self.fledglings -= 1
        else:
            # Defer replacements until entering a breeding month
            take = min(len(dead_agents), self.fledglings)
            self.pending_recruits += take
            self.fledglings -= take

        # Seasonal recruitment trigger: when entering a breeding month
        if self.replacement_policy != "immediate":
            entering_breeding = (self._last_month not in BREEDING_MONTHS) and (self.month in BREEDING_MONTHS)
            if entering_breeding and self.pending_recruits > 0:
                for _ in range(self.pending_recruits):
                    new_pos = (random.uniform(0, 99), random.uniform(0, 99))
                    new_id = max([a.unique_id for a in self.schedule.agents], default=0) + 1
                    new_agent = HarrierAgent(new_id, self, new_pos, breeding=True)
                    self.schedule.add(new_agent)
                    self.space.place_agent(new_agent, new_pos)
                self.pending_recruits = 0

        self._last_month = self.month
        self.datacollector.collect(self)

    # ---------------------
    # Wake multiplier helper (<= 1.0)
    # ---------------------
    def _wake_multiplier(self, pos: np.ndarray) -> float:
        if not self.wake_loss or self._turbine_positions.size == 0:
            return 1.0
        diffs = self._turbine_positions - pos
        dists = np.sqrt(np.einsum("ij,ij->i", diffs, diffs))
        decay = np.exp(-dists / max(self.wake_decay, 1e-6))
        penalty = self.wake_coeff * float(decay.sum())
        return float(np.clip(1.0 - penalty, 0.1, 1.0))