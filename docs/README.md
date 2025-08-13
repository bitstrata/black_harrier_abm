# Detailed README: Black Harrier ABM Project

This project implements an ABM using Mesa to simulate Black Harrier movements and collision risks with WEFs, based on *Black Harriers and Wind Energy* guidelines (Simmons et al., 2020).

## Key Features
- GPS data integration for Markov transitions.
- Bayesian updating for collision probabilities.
- Solara visualization for browser-based monitoring.
- Mitigation strategies (blade painting, shutdown, habitat management).
- Outputs: Simulation results and curtailment schedules.

## Data Requirements
- data/harrier_gps.csv: GPS flight data (harrier_id, timestamp, lat, lon, alt, speed).
- data/lidar_dem.geojson: LiDAR terrain.
- data/weather.nc: Hourly wind/pressure.
- data/turbines.geojson: Turbine locations (lat, lon, hub_height, blade_radius).
- data/nests_roosts.csv: Locations of nests, roosts, hunting areas (lat, lon, type).

## Running the Model
See usage.md.