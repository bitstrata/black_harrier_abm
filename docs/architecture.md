# Architecture: Black Harrier ABM

## Overview
- **src/data_processing.py**: Processes GPS (DBSCAN, Markov transitions), LiDAR, weather, turbine data, builds graph.
- **src/models.py**: HarrierAgent (movement, collision, breeding) and HarrierModel (simulation, data collection).
- **src/bayesian_utils.py**: Bayesian updating for collision risk (Beta distribution).
- **src/visualization.py**: Solara browser-based visualization of harriers, turbines, nests/roosts.
- **src/main.py**: Runs simulation, outputs results/curtailment.

## OOP Design
- HarrierAgent: Encapsulates harrier state (pos, height, breeding) and behaviors (move, check_collision, breed).
- HarrierModel: Manages agents, graph, space, and collectors.

## Flow
1. Process data → Build graph.
2. Initialize model with agents in ContinuousSpace.
3. Step: Update month, Bayesian probabilities, agent moves/collisions/breeding.
4. Collect data and visualize with Solara.

## Dependencies
See requirements.txt.