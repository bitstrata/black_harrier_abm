from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector
import pandas as pd
import random
import math
from src.config import BSA_HEIGHT, MIGRATION_HEIGHT, BREEDING_MONTHS, MIGRATION_MONTHS, FORAGING_RANGE, NON_BREEDING_RANGE, DISPLACEMENT_RADIUS, NEST_FAIL_PROB, ROOST_BUFFER_COMMUNAL, ROOST_BUFFER_SINGLE, NEST_BUFFER_VERY_HIGH, MITIGATION_BLADE_PAINT, MITIGATION_SHUTDOWN, PREY_REDUCTION_FACTOR
from src.bayesian_utils import bayesian_update_collision_prob
from src.data_processing import process_gps_data, process_lidar_data, process_weather_data, process_turbine_data, build_graph, Point

# Harrier Agent
class HarrierAgent(Agent):
    def __init__(self, unique_id, model, pos, breeding=False):
        super().__init__(unique_id, model)
        self.pos = pos
        self.height = random.uniform(0, 100)
        self.breeding = breeding
        self.alive = True
        self.nest = random.choice(self.model.nests) if breeding else None
        self.breeding_month = random.choice(BREEDING_MONTHS) if breeding else None
        self.energy = 100
        self.current_node = None

    def move(self):
        if not self.alive:
            return
        month = self.model.month
        G = self.model.graph
        transition_probs = self.model.transition_probs
        if not self.current_node:
            self.current_node = min(G.nodes, key=lambda n: Point(G.nodes[n]['pos']).distance(Point(self.pos)))
        if month in BREEDING_MONTHS and self.breeding:
            max_range = FORAGING_RANGE
            self.height = random.uniform(BSA_HEIGHT[0], BSA_HEIGHT[1]) if random.random() < 0.35 else random.uniform(0, 30)
        elif month in MIGRATION_MONTHS:
            max_range = NON_BREEDING_RANGE
            self.height = random.uniform(MIGRATION_HEIGHT[0], MIGRATION_HEIGHT[1])
        else:
            max_range = NON_BREEDING_RANGE
            self.height = random.uniform(0, 30)
        neighbors = list(G.neighbors(self.current_node))
        if not neighbors:
            return
        weights = []
        for n in neighbors:
            prob = transition_probs.get((month, self.current_node, n), 1 / len(neighbors))
            edge = G[self.current_node][n]
            thermal = edge['thermal']
            risk = edge['turbine_risk'] if edge['turbine_active'] else 0
            weight = prob * thermal / (1 + risk)
            weights.append(weight)
        next_node = random.choices(neighbors, weights=weights, k=1)[0]
        new_pos = G.nodes[next_node]['pos']
        for tx, ty in self.model.turbines:
            if math.sqrt((new_pos[0] - tx)**2 + (new_pos[1] - ty)**2) < DISPLACEMENT_RADIUS:
                return
        self.pos = new_pos
        self.current_node = next_node
        self.energy -= 1

    def check_collision(self):
        if not self.alive:
            return False
        month = self.model.month
        if (month in BREEDING_MONTHS and BSA_HEIGHT[0] <= self.height <= BSA_HEIGHT[1]) or \
           (month in MIGRATION_MONTHS and MIGRATION_HEIGHT[0] <= self.height <= MIGRATION_HEIGHT[1]):
            for tx, ty in self.model.turbines:
                if math.sqrt((self.pos[0] - tx)**2 + (self.pos[1] - ty)**2) < 1:
                    for nx, ny in self.model.nests:
                        if math.sqrt((self.pos[0] - nx)**2 + (self.pos[1] - ny)**2) < NEST_BUFFER_VERY_HIGH:
                            return False
                    for rx, ry in self.model.communal_roosts:
                        if math.sqrt((self.pos[0] - rx)**2 + (self.pos[1] - ry)**2) < ROOST_BUFFER_COMMUNAL:
                            return False
                    for rx, ry in self.model.single_roosts:
                        if math.sqrt((self.pos[0] - rx)**2 + (self.pos[1] - ty)**2) < ROOST_BUFFER_SINGLE:
                            return False
                    if random.random() > self.model.avoidance_rate:
                        collision_prob = self.model.collision_prob
                        if random.random() < MITIGATION_BLADE_PAINT:
                            collision_prob *= (1 - 0.71)
                        if random.random() < MITIGATION_SHUTDOWN and month in BREEDING_MONTHS:
                            collision_prob *= (1 - 0.50)
                        if random.random() < PREY_REDUCTION_FACTOR:
                            collision_prob *= (1 - 0.50)
                        if random.random() < collision_prob:
                            self.alive = False
                            return True
        return False

    def breed(self):
        if not self.alive or not self.breeding or self.model.month not in BREEDING_MONTHS:
            return 0
        if random.random() < NEST_FAIL_PROB and self.unique_id % 2 == 0:
            return 0
        return 2 if random.random() < 0.7 else 0

# ABM Model
class HarrierModel(Model):
    def __init__(self, gps_file, lidar_file, weather_file, turbine_file):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.month = 1
        self.nests = [(random.uniform(20, 80), random.uniform(20, 80)) for _ in range(5)]
        self.communal_roosts = [(50, 50)]
        self.single_roosts = [(random.uniform(0, 100-1), random.uniform(0, 100-1)) for _ in range(10)]
        self.turbines = [(random.uniform(0, 100-1), random.uniform(0, 100-1)) for _ in range(60)]
        waypoints, agents, self.transition_probs = process_gps_data(gps_file)
        nodes = process_lidar_data(lidar_file)
        thermal_data = process_weather_data(weather_file)
        turbines = process_turbine_data(turbine_file)
        self.graph = build_graph(waypoints, nodes, turbines, thermal_data)
        self.space = ContinuousSpace(100, 100, torus=False)
        self.avoidance_rate = 0.935  # AVOIDANCE_RATE_PRIOR
        self.collision_prob = 0.15   # COLLISION_PROB_PRIOR
        for i, row in agents.iterrows():
            pos = (row['initial_pos'].x, row['initial_pos'].y)
            breeding = i < 120
            agent = HarrierAgent(i, self, pos, breeding)
            self.schedule.add(agent)
            self.space.place_agent(agent, pos)
        self.datacollector = DataCollector(
            model_reporters={
                "Population": lambda m: sum(1 for a in m.schedule.agents if a.alive),
                "Fatalities": lambda m: m.fatalities,
                "Fledglings": lambda m: m.fledglings,
                "Collision_Prob": lambda m: m.collision_prob
            },
            agent_reporters={
                "Position": lambda a: a.pos,
                "Height": lambda a: a.height,
                "Alive": lambda a: a.alive
            }
        )
        self.fatalities = 0
        self.fledglings = 0
        self.curtailment_schedule = {t: [] for t in self.turbines}
        self.gps_data = pd.read_csv(gps_file)

    def step(self):
        self.month = (self.month % 12) + 1
        self.fatalities = 0
        self.fledglings = 0
        self.collision_prob = bayesian_update_collision_prob(self.collision_prob, self.gps_data, process_turbine_data("turbines.geojson"))
        for agent in self.schedule.agents:
            agent.move()
            if agent.check_collision():
                self.fatalities += 1
                for tx, ty in self.turbines:
                    if math.sqrt((agent.pos[0] - tx)**2 + (agent.pos[1] - ty)**2) < 1:
                        self.curtailment_schedule[(tx, ty)].append((self.month, self.schedule.steps % 24))
            self.fledglings += agent.breed()
        dead_agents = [a for a in self.schedule.agents if not a.alive]
        for agent in dead_agents:
            if self.fledglings > 0:
                new_pos = (random.uniform(0, 100-1), random.uniform(0, 100-1))
                new_agent = HarrierAgent(agent.unique_id, self, new_pos, agent.breeding)
                self.schedule.add(new_agent)
                self.space.place_agent(new_agent, new_pos)
                self.fledglings -= 1
        self.datacollector.collect(self)