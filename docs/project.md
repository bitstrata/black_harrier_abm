# Black Harrier ABM: Project Scope, Cost, and Milestones

This document outlines the scope, cost estimate, timeline, and milestones for the Black Harrier Agent-Based Model (ABM) project, designed to analyze Black Harrier movement patterns and wind turbine collision risks in the Eastern Cape, South Africa, particularly around Port Elizabeth. The project leverages client-provided datasets and synthetic data generation to deliver a lean, cost-effective solution.

## Cost Estimate
- **Budget Constraint**: Fixed at $25,000/phase ($100,000 total for 4 phases), significantly lower than the original $500,250 and optimized $356,100, achieved by:
  - **Excluding Data Collection**: Client-provided GPS, LiDAR, weather, and turbine datasets eliminate acquisition costs ($5,000–$7,000 in prior estimates). Synthetic data generation (`data/generate_*.py`) supports testing.
  - **Lean Team**: Reduced to 1 Data Scientist (0.5 FTE, $38,400), 1 GIS Specialist (0.3 FTE, $20,160), 1 Ornithologist (0.2 FTE, $17,280), 1 PM (0.2 FTE, $23,040), using South African rates ($35–$60/hr vs. $50–$80/hr U.S. rates) to align with local expertise (e.g., University of Cape Town, BirdLife SA).
  - **Minimal Hardware/Software**: Client-provided workstations ($1,000 leasing) and free/open-source tools (QGIS, Gephi, Python with `mesa==2.3.4`, `xarray==2023.12.0`, `cftime>=1.6.3`, $1,000) reduce costs.
  - **Virtual Engagement**: One virtual workshop ($500) eliminates travel costs ($4,000 in prior estimate).
  - **Contingency**: 10% ($10,120) covers unexpected needs (e.g., complex GPS processing or performance optimization).
- **Optional Validation**: $13,440 (0.2 FTE Ornithologist, 3 months, $45/hr, 192 hrs), grant-funded (e.g., BirdLife SA, SANEDI, Rufford Foundation), ensuring no client cost.
- **Comparison**: The $100,000 budget aligns with lower-end wildlife-wind energy studies ($50,000–$150,000, e.g., global raptor review) and is below mid-range GPS-based studies ($200,000–$500,000, e.g., griffon vulture) due to no data collection and synthetic data use.

## Project Timeline
- **Phase 1 (Months 1–3, $25,000)**:
  - **Tasks**: Analyze client-provided GPS data (DBSCAN clustering for Markov transitions), LiDAR, weather, and turbine data; design ABM with Markov/Bayesian components; implement synthetic data generation (`data/generate_*.py`) for testing.
  - **Deliverables**: Processed datasets, ABM design document, prototype graph (Gephi), synthetic data scripts (`harrier_gps.csv`, `lidar_dem.geojson`, `weather.nc`, `optimized_turbines.geojson`).
  - **Use**: Client confirms data suitability and model approach.
- **Phase 2 (Months 4–6, $25,000)**:
  - **Tasks**: Implement ABM (`mesa==2.3.4`) with GPS-derived Markov transitions and Bayesian updating (Beta distribution). Simulate 100 years (1,000 harriers, 60 turbines). Optimize turbine placement based on wind speed (`optimize_turbine_placement.py`).
  - **Deliverables**: ABM script (`main.py`, `src/models.py`), initial results (`simulation_results.csv`), curtailment schedule (`curtailment_schedule.csv`).
  - **Use**: Client tests outputs for mitigation planning.
- **Phase 3 (Months 7–9, $25,000)**:
  - **Tasks**: Calibrate model with Eastern Cape WEF data (e.g., 5 fatalities/4 years), optimize transitions/priors, develop QGIS risk maps and Gephi visualizations.
  - **Deliverables**: Refined ABM, visualizations, mitigation report.
  - **Use**: Client assesses high-risk zones and mitigation strategies.
- **Phase 4 (Months 10–12, $25,000)**:
  - **Tasks**: Validate model with client-provided field data, conduct virtual stakeholder workshop, finalize documentation (`docs/usage.md`, `docs/project_scope.md`).
  - **Deliverables**: Validated results, final curtailment schedule, report, presentation.
  - **Use**: Client implements or proceeds to validation.
- **Optional Validation (Months 13–15, $13,440, grant-funded)**:
  - **Tasks**: Analyze client-provided field data (e.g., carcass surveys), update model, prepare publication draft.
  - **Deliverables**: Validated model, updated outputs, publication draft.
  - **Use**: Client deploys or expands to other WEFs.

## Alignment with Similar Studies
- **Cost Comparison**: The $100,000 budget matches review-based projects ($50,000–$150,000, e.g., global raptor review) and is below GPS-based studies ($200,000–$500,000, e.g., griffon vulture) due to synthetic data and no data collection.
- **Scope Fit**: Retains core functionality (GPS-driven ABM, curtailment schedules) aligned with Black Harriers and Wind Energy guidelines (Simmons et al., 2020), comparable to simpler models (e.g., seabird assessment, $150,000–$400,000) but with real-time GPS integration.

## Grant Funding for Optional Validation
- **Sources**:
  - BirdLife International ($5,000–$20,000): Funds Black Harrier conservation (apply via rolling grants, reference IUCN Red List status).
  - Rufford Foundation ($5,000–$10,000): Small grants for endangered species research (apply online, Q1 2026).
  - SANEDI ($5,000–$10,000): Supports renewable energy environmental studies (apply Q1 2026).
- **Strategy**: Secure $13,440 from BirdLife ($10,000) and Rufford ($3,440) by Month 10, covering validation costs. Client provides field data (e.g., fatality records).
- **Fit**: High, as validation aligns with conservation goals and leverages Eastern Cape WEF data.

## Risks and Mitigation
- **Data Quality**: Incomplete GPS data (e.g., missing altitude) may limit Markov/Bayesian accuracy. Mitigated by synthetic data generation (`data/generate_*.py`) with realistic Port Elizabeth topography and wind patterns.
- **Resource Constraints**: Lean team (0.2–0.5 FTE) may delay tasks. Mitigated by parallel workflows and client feedback.
- **Validation**: Limited field data may rely on proxy collisions. Mitigated by client-provided fatality records (e.g., 5 in 4 years).
- **Cost Overruns**: 10% contingency ($10,120) covers unexpected needs (e.g., performance optimization for `weather.nc`).
- **Performance**: Generating `weather.nc` (100x100x8760) is memory-intensive. Mitigated by reducing `n_points` to 50 if needed.
- **Software Compatibility**: Python 3.9 issues with `solara>=1.35.0` or `xarray>=2024.6.0`. Mitigated by pinning `solara==1.32.0`, `xarray==2023.12.0`, and adding `cftime>=1.6.3`.

## Conservation Impact
- Delivers precise curtailment schedules (e.g., breeding/migration periods) to reduce fatalities (<3/year to avoid collapse) with minimal energy loss (~0.07%, de Lucas et al., 2012).
- Supports Jeffreys Bay Wind Farm’s tracking initiatives and BirdLife SA’s guidelines, enhancing environmental stewardship.

## Recent Code Changes
- **Moved `main.py`**: Relocated to project root for simpler execution (`python main.py`).
- **Runtime Data Generation**: Synthetic datasets are generated at runtime as temporary files, cleaned up post-simulation to avoid GitHub storage.
- **Seed Management**: Centralized `seed=42` in `main.py`, passed to `data/generate_*.py` for repeatability.
- **Weather Fixes**: Updated `generate_weather_nc.py` to use `freq="h"`, set `ds["time"].attrs["units"] = "hours since 2023-01-01 00:00:00"`, and encode time correctly to avoid `TypeError` and `OutOfBoundsTimedelta`.
- **Dependencies**: Added `cftime>=1.6.3` for `xarray` datetime handling.
- **Bayesian Fixes**: Added imports for `Point` and `BSA_HEIGHT` in `bayesian_utils.py`.

## Next Steps
- **Data Confirmation**: Client provides GPS, LiDAR, weather, and turbine datasets by Month 1, specifying format (e.g., `harrier_gps.csv` with `harrier_id`, `timestamp`, `lat`, `lon`, `alt`, `speed`).
- **Funding**: Confirm interest in pursuing grants (BirdLife, Rufford, SANEDI) for validation phase by Month 9.
- **Customization**: Specify WEF focus (e.g., Eastern Cape), visualization preferences (e.g., QGIS maps), or mitigation scenarios (e.g., blade painting variants).
- **Deliverable Format**: Request full `.ipynb` with ABM script and markdown or additional outputs (e.g., Gephi networks).
- **Testing**: Add unit tests in `tests/` for data generation and Bayesian updates.
- **Documentation**: Update `docs/usage.md` with any future changes.

Please confirm datasets, funding preferences, or specific requirements to finalize the plan!