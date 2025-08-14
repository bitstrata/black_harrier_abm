# Architecture: Black Harrier ABM

## Overview
The Black Harrier Agent-Based Model (ABM) simulates harrier movement and wind turbine collision risks in Port Elizabeth, Eastern Cape, using client-provided or synthetic datasets (GPS, LiDAR, weather, turbines). The model integrates Markov transitions, Bayesian updating, and spatial analysis to generate curtailment schedules.

### Key Files
- **main.py**: Entry point in the project root. Generates synthetic datasets at runtime, runs the simulation, outputs results (`simulation_results.csv`, `curtailment_schedule.csv`), and triggers visualization.
- **src/data_processing.py**: Processes GPS data (DBSCAN clustering for Markov transitions), LiDAR topography, weather, and turbine data; builds a `networkx` graph for movement.
- **src/models.py**: Defines `HarrierAgent` (movement, collision, breeding) and `HarrierModel` (manages agents, space, data collection).
- **src/bayesian_utils.py**: Updates collision probabilities using Bayesian methods (Beta distribution).
- **src/visualization.py**: Generates Solara browser-based visualizations of harriers, turbines, nests, and roosts.
- **src/config.py**: Defines simulation parameters (e.g., `NUM_TURBINES=60`, `BSA_HEIGHT=(30, 130)`).
- **data/generate_harrier_gps.py**: Generates synthetic GPS data (~15,000 rows, 10 harriers) with clustering near nests during breeding months.
- **data/generate_lidar_dem.py**: Generates synthetic LiDAR topography (10,000 points, 100x100 grid, elevations 0–500 m, slopes 0–15°).
- **data/generate_weather_nc.py**: Generates synthetic weather data (100x100x8760, wind speed 0–10 m/s influenced by topography, pressure 900–1100 hPa).
- **data/optimize_turbine_placement.py**: Optimizes 60 turbine locations based on wind speed with 500 m spacing.

## OOP Design
- **HarrierAgent**: Encapsulates harrier state (position, height, breeding status) and behaviors (move via Markov transitions, check collisions, breed based on season).
- **HarrierModel**: Manages agents, `ContinuousSpace` (from `mesa`), `networkx` graph for movement, and data collectors for population, fatalities, and collision probabilities.

## Flow
1. **Initialize**: `main.py` sets pseudo-random seed (`seed=42`) and calls data generation scripts (`data/generate_*.py`) to create temporary files (`harrier_gps.csv`, `lidar_dem.geojson`, `weather.nc`, `optimized_turbines.geojson`).
2. **Process Data**: `data_processing.py` processes GPS (DBSCAN for waypoints), LiDAR, weather, and turbine data; builds a `networkx` graph for movement transitions.
3. **Initialize Model**: `HarrierModel` loads processed data, places agents in `ContinuousSpace`, and sets initial conditions (e.g., 1,000 harriers, 60 turbines).
4. **Step**: For each month (100 years = 1,200 steps):
   - Update month and environmental conditions (e.g., wind, breeding season).
   - Update collision probabilities via `bayesian_utils.py` (Beta distribution).
   - Agents move (Markov transitions), check collisions (based on `BSA_HEIGHT`), and breed (seasonal).
5. **Collect and Visualize**: Collect data (population, fatalities, collision probability) and visualize annually using Solara (`visualization.py`) at `http://localhost:8765`.
6. **Output**: Save results (`simulation_results.csv`) and curtailment schedules (`curtailment_schedule.csv`); clean up temporary files.

## Dependencies
See `requirements.txt`:
- `mesa==2.3.4`: ABM framework.
- `pandas>=2.0.3`: Data handling.
- `geopandas>=0.14.0`: Geospatial data processing.
- `numpy>=1.24.3`: Numerical computations.
- `networkx==3.2.1`: Graph-based movement.
- `solara>=1.32.0`: Visualization.
- `xarray==2023.12.0`: Weather data handling.
- `scikit-learn>=1.3.2`: DBSCAN clustering.
- `scipy>=1.11.4`: Optimization and filtering.
- `noise>=1.2.2`: Topography generation.
- `cftime>=1.6.3`: `xarray` datetime support.

## Recent Changes
- **Moved `main.py`**: Relocated from `src/` to project root for simpler execution (`python main.py`).
- **Runtime Data Generation**: Added `data/generate_*.py` scripts to generate temporary datasets at runtime, cleaned up post-simulation to avoid GitHub storage.
- **Seed Management**: Centralized `seed=42` in `main.py`, passed to data generation scripts for repeatability.
- **Weather Fixes**: Updated `generate_weather_nc.py` to use `freq="h"`, set `ds["time"].attrs["units"] = "hours since 2023-01-01 00:00:00"`, and encode time correctly to avoid `TypeError` and `OutOfBoundsTimedelta`.
- **Bayesian Fixes**: Added imports for `Point` (from `data_processing.py`) and `BSA_HEIGHT` (from `config.py`) in `bayesian_utils.py`.
- **Dependencies**: Added `cftime>=1.6.3` for robust `xarray` datetime handling.

## Notes
- **Performance**: Generating `weather.nc` (100x100x8760) is memory-intensive. Reduce `n_points` to 50 in `generate_lidar_dem.py` and `generate_weather_nc.py` if needed.
- **Compatibility**: Uses Python 3.9. If issues arise with `solara>=1.35.0` or `xarray>=2024.6.0`, pin to `solara==1.32.0` and `xarray==2023.12.0`.