import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
from src.config import BREEDING_MONTHS

def generate_harrier_gps(seed=42, num_harriers=10, points_per_harrier=1500):
    """
    Generate synthetic GPS tracks for harriers, simulating breeding and non-breeding behavior.
    
    Returns:
        Path to CSV file containing simulated GPS data.
    """
    np.random.seed(seed)

    # Constants
    START_DATE = datetime(2023, 1, 1)
    LAT_MIN, LAT_MAX = -34.2, -33.6
    LON_MIN, LON_MAX = 25.3, 25.9
    NEST_LOCATIONS = [(-33.920, 25.620), (-33.880, 25.580)]

    all_data = []

    for harrier_id in range(1, num_harriers + 1):
        current_time = START_DATE
        current_pos = np.random.uniform([LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX])

        for _ in range(points_per_harrier):
            month = current_time.month
            timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")

            if month in BREEDING_MONTHS:
                # Close to nest during breeding
                nest_lat, nest_lon = NEST_LOCATIONS[np.random.randint(len(NEST_LOCATIONS))]
                lat = np.random.normal(nest_lat, 0.005)
                lon = np.random.normal(nest_lon, 0.005)
                alt = np.random.uniform(20, 50)
                speed = np.random.uniform(2, 8)
            else:
                # Roaming outside breeding
                lat = np.clip(current_pos[0] + np.random.uniform(-0.01, 0.01), LAT_MIN, LAT_MAX)
                lon = np.clip(current_pos[1] + np.random.uniform(-0.01, 0.01), LON_MIN, LON_MAX)
                alt = np.random.uniform(60, 100)
                speed = np.random.uniform(5, 15)

            all_data.append((harrier_id, timestamp, lat, lon, alt, speed))

            current_pos = (lat, lon)
            current_time += timedelta(hours=np.random.randint(1, 3))

    # Create DataFrame
    df = pd.DataFrame(all_data, columns=['harrier_id', 'timestamp', 'lat', 'lon', 'alt', 'speed'])

    # Write to a temporary CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name