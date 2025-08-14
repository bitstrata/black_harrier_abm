# Usage Guide for Black Harrier ABM

This guide explains how to set up and run the Black Harrier Agent-Based Model (ABM) for simulating harrier movement and wind turbine collision risks in Port Elizabeth, Eastern Cape.

## Prerequisites
- **Python**: 3.9
- **Dependencies**: Listed in `requirements.txt`:
  - `mesa==2.3.4`
  - `pandas>=2.0.3`
  - `geopandas>=0.14.0`
  - `numpy>=1.24.3`
  - `networkx==3.2.1`
  - `solara>=1.32.0`
  - `xarray==2023.12.0`
  - `scikit-learn>=1.3.2`
  - `scipy>=1.11.4`
  - `noise>=1.2.2`
  - `cftime>=1.6.3`

## Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/markbenjamindahl/black_harrier_abm.git
   cd black_harrier_abm
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Simulation
Run the simulation from the project root:
```bash
python main.py
```

### What Happens
- **Data Generation**: Temporary files are generated using scripts in `data/` with a fixed seed (42) for repeatability:
  - `harrier_gps.csv`: ~15,000 GPS points for 10 harriers.
  - `lidar_dem.geojson`: 10,000 points (100x100) with Port Elizabeth topography.
  - `weather.nc`: 100x100x8760 weather data with topography-influenced wind.
  - `optimized_turbines.geojson`: 60 turbines optimized for wind speed.
- **Simulation**: Runs the ABM (`HarrierModel`) for 100 years, simulating 1,000 harriers and 60 turbines.
- **Outputs**: Produces `simulation_results.csv` (population, fatalities, collision probability) and `curtailment_schedule.csv` (turbine shutdown times).
- **Visualization**: Displays a Solara dashboard at `http://localhost:8765` (if compatible).
- **Cleanup**: Temporary files are deleted after the simulation.

## Key Files
- **main.py**: Entry point, calls data generation and runs the ABM.
- **src/models.py**: Defines `HarrierModel` and agent behaviors.
- **src/data_processing.py**: Processes GPS, LiDAR, weather, and turbine data.
- **src/bayesian_utils.py**: Updates collision probabilities using Bayesian methods.
- **src/visualization.py**: Generates Solara visualizations.
- **src/config.py**: Defines parameters (e.g., `NUM_TURBINES=60`, `BSA_HEIGHT=(30, 130)`).
- **data/generate_*.py**: Generates synthetic datasets at runtime.

## Recent Changes
- **Moved `main.py`**: Relocated from `src/` to project root for simpler execution (`python main.py`).
- **Runtime Data Generation**: Datasets are generated as temporary files using `tempfile` to avoid GitHub storage.
- **Seed Management**: Centralized `seed=42` in `main.py`, passed to `data/generate_*.py` scripts.
- **Weather Fixes**: Updated `generate_weather_nc.py` to use `freq="h"`, set `time` attributes (`ds["time"].attrs["units"]`), and encode time correctly to avoid `TypeError` and `OutOfBoundsTimedelta`.
- **Dependencies**: Added `cftime>=1.6.3` for robust `xarray` datetime handling.
- **Bayesian Fixes**: Added imports for `Point` and `BSA_HEIGHT` in `bayesian_utils.py`.

## Troubleshooting
- **Solara**: If visualization fails, use `solara==1.32.0` or comment out `HarrierVisualization` in `main.py`.
- **Performance**: If `weather.nc` is slow, reduce `n_points` to 50 in `generate_lidar_dem.py` and `generate_weather_nc.py`.
- **DBSCAN**: If waypoints are empty, set `eps=0.1` in `data_processing.py`.

## Customization
- **Seed**: Modify `seed` in `main.py` for different random runs.
- **Grid Size**: Adjust `n_points` in `generate_lidar_dem.py` and `generate_weather_nc.py`.
- **Turbines**: Change `NUM_TURBINES` in `config.py`.