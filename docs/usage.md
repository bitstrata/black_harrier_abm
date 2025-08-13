# Usage Guide: Black Harrier ABM

## Setup
1. Activate venv: `source .venv/bin/activate`.
2. Place data files in `data/`.
3. Run simulation: `python main.py .

## Outputs
- simulation_results.csv: Population, fatalities, fledglings, collision probability.
- curtailment_schedule.csv: Turbine shutdown recommendations (month, hour).
- Solara visualization: Run in browser for interactive maps.

## Testing
Run unit tests: `pytest tests/`.