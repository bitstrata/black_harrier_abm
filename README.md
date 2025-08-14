# Black Harrier ABM

Agent-Based Model (ABM) for analyzing Black Harrier movement patterns and wind turbine collision risks in the Eastern Cape, South Africa, particularly around Port Elizabeth. The model uses GPS data, LiDAR-derived topography, weather data, and turbine locations to simulate harrier behavior and generate curtailment schedules to minimize collisions while maintaining wind farm efficiency.

## Project Structure
- `main.py`: Entry point for running the simulation, now located in the project root.
- `src/`: Contains core modules (`models.py`, `data_processing.py`, `visualization.py`, `bayesian_utils.py`, `config.py`).
- `data/`: Contains scripts to generate synthetic datasets (`generate_harrier_gps.py`, `generate_lidar_dem.py`, `generate_weather_nc.py`, `optimize_turbine_placement.py`).
- `docs/`: Documentation, including `usage.md` and `project_scope.md`.
- `tests/`: Unit tests (to be added).
- `requirements.txt`: Python dependencies.

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
   Dependencies include `mesa==2.3.4`, `pandas>=2.0.3`, `geopandas>=0.14.0`, `numpy>=1.24.3`, `networkx==3.2.1`, `solara>=1.32.0`, `xarray==2023.12.0`, `scikit-learn>=1.3.2`, `scipy>=1.11.4`, `noise>=1.2.2`, `cftime>=1.6.3`.

4. **Run the Simulation**:
   ```bash
   python main.py
   ```
   This generates temporary datasets (`harrier_gps.csv`, `lidar_dem.geojson`, `weather.nc`, `optimized_turbines.geojson`), runs the ABM, produces `simulation_results.csv` and `curtailment_schedule.csv`, and displays a Solara visualization at `http://localhost:8765` (if compatible).

## Recent Changes
- **Moved `main.py`**: Relocated from `src/` to project root for simpler execution (`python main.py`).
- **Runtime Data Generation**: Synthetic datasets are generated at runtime using scripts in `data/`, stored as temporary files via `tempfile`, and cleaned up post-simulation to avoid GitHub storage.
- **Pseudo-Random Seed**: Centralized `seed=42` in `main.py`, passed to data generation scripts for repeatability.
- **Weather Data Fix**: Updated `generate_weather_nc.py` to use `freq="h"` (fixing `FutureWarning`) and set `time` attributes/encoding correctly (`ds["time"].attrs["units"] = "hours since 2023-01-01 00:00:00"`) to avoid `TypeError` and `OutOfBoundsTimedelta`.
- **Dependencies**: Added `cftime>=1.6.3` to `requirements.txt` for robust `xarray` datetime handling.
- **Bayesian Utils**: Fixed undefined `Point` and `BSA_HEIGHT` in `bayesian_utils.py` by adding imports from `data_processing.py` and `config.py`.

## Data Generation
- **harrier_gps.csv**: ~15,000 rows for 10 harriers, with clustering near nests during breeding months (July, August, November, December).
- **lidar_dem.geojson**: 10,000 points (100x100 grid) with realistic Port Elizabeth topography (elevations 0–500 m, slopes 0–15°, ~50% > 5°).
- **weather.nc**: 100x100x8760 (lat, lon, time) with `wind_speed` (0–10 m/s, accelerated over ridges), `pressure` (900–1100 hPa), `thermal`, `turbine_active`.
- **optimized_turbines.geojson**: 60 turbines optimized for wind speed with 500 m spacing.

## Next Steps
- Verify visualization at `http://localhost:8765`.
- Add unit tests in `tests/` for data generation and Bayesian updates.
- Update `docs/usage.md` and `docs/project_scope.md` with detailed instructions.
- Confirm client-provided datasets (GPS, LiDAR, weather, turbines) for Phase 1.

## Troubleshooting
- **Solara Issues**: If visualization fails, use `solara==1.32.0` or comment out `HarrierVisualization` in `main.py`.
- **Performance**: If `weather.nc` generation is slow, reduce `n_points` to 50 in `generate_lidar_dem.py` and `generate_weather_nc.py`.
- **DBSCAN**: If waypoints are empty, increase `eps` to 0.1 in `data_processing.py`.