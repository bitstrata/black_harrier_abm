# Model Parameters for Black Harrier ABM
NUM_HARRIERS = 1000  # Global population (~1000 mature individuals)
NUM_TURBINES = 60  # Eastern Cape WEF
GRID_SIZE = 100  # 100x100 km grid
NEST_BUFFER_VERY_HIGH = 3  # 3 km very high sensitivity
NEST_BUFFER_HIGH = 5  # 5 km high sensitivity
ROOST_BUFFER_COMMUNAL = 4  # 3-5 km for communal roosts
ROOST_BUFFER_SINGLE = 2  # 1-3 km for single roosts
BSA_HEIGHT = (30, 130)  # Blade-swept area (30-130m)
MIGRATION_HEIGHT = (60, 100)  # Migration flight height
FORAGING_RANGE = 16.4  # Breeding foraging range (km)
NON_BREEDING_RANGE = 18.1  # Non-breeding foraging range (km)
AVOIDANCE_RATE_PRIOR = 0.935  # Prior avoidance rate (Schaub et al., 2019)
COLLISION_PROB_PRIOR = 0.15  # Prior collision probability during breeding
MITIGATION_BLADE_PAINT = 0.71  # 71% fatality reduction (Stokke et al., 2017)
MITIGATION_SHUTDOWN = 0.50  # 50% fatality reduction (de Lucas et al., 2012)
PREY_REDUCTION_FACTOR = 0.5  # 50% prey reduction
DISPLACEMENT_RADIUS = 0.5  # 500m avoidance radius
NEST_FAIL_PROB = 0.3  # Nest failure if male dies
BREEDING_MONTHS = [7, 8, 11, 12]  # July-August, November-December
MIGRATION_MONTHS = [1, 2, 4, 5, 6]  # December-January, April-June
WIND_THRESHOLD = 3  # Turbine operation threshold (m/s)
TURBINE_POWER_CURVE = [
    (0, 0),
    (3, 0),      # Cut-in speed
    (5, 200),
    (8, 1000),
    (12, 2000),  # Rated power
    (25, 2000),  # Cut-out speed
]