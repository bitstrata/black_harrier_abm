# Usage Guide: Black Harrier ABM

## Setup
1. Activate venv: `source .venv/bin/activate`.
2. Place data files in `data/`.
3. Run simulation: `python src/main.py --gps_file data/harrier_gps.csv --lidar_file data/lidar_dem.geojson --weather_file data/weather.nc --turbine_file data/turbines.geojson`.

## Outputs
- simulation_results.csv: Population, fatalities, fledglings, collision probability.
- curtailment_schedule.csv: Turbine shutdown recommendations (month, hour).
- Solara visualization: Run in browser for interactive maps.

## Testing
Run unit tests: `pytest tests/`.