import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
from src.config import BREEDING_MONTHS

def generate_harrier_gps(seed):
    np.random.seed(seed)
    num_harriers = 10
    points_per_harrier = 1500
    start_date = datetime(2023, 1, 1)
    nest_locations = [(-33.920, 25.620), (-33.880, 25.580)]
    data = []
    for harrier_id in range(1, num_harriers + 1):
        current_time = start_date
        current_pos = np.random.uniform([-34.2, 25.3], [-33.6, 25.9])
        for i in range(points_per_harrier):
            timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
            month = current_time.month
            if month in BREEDING_MONTHS:
                nest = nest_locations[np.random.choice(len(nest_locations))]
                lat = np.random.normal(nest[0], 0.005)
                lon = np.random.normal(nest[1], 0.005)
                alt = np.random.uniform(20, 50)
                speed = np.random.uniform(2, 8)
            else:
                lat = current_pos[0] + np.random.uniform(-0.01, 0.01)
                lon = current_pos[1] + np.random.uniform(-0.01, 0.01)
                lat = np.clip(lat, -34.2, -33.6)
                lon = np.clip(lon, 25.3, 25.9)
                alt = np.random.uniform(60, 100)
                speed = np.random.uniform(5, 15)
            data.append([harrier_id, timestamp, lat, lon, alt, speed])
            current_pos = [lat, lon]
            current_time += timedelta(hours=np.random.randint(1, 3))
    df = pd.DataFrame(data, columns=['harrier_id', 'timestamp', 'lat', 'lon', 'alt', 'speed'])
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name