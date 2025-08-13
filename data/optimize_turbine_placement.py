import geopandas as gpd
import numpy as np
import xarray as xr
from scipy.optimize import differential_evolution
import tempfile
from src.config import NUM_TURBINES

def optimize_turbine_placement(weather_file, seed):
    np.random.seed(seed)
    ds = xr.open_dataset(weather_file)
    avg_wind_speed = ds['wind_speed'].mean(dim="time").values
    lat_grid, lon_grid = np.meshgrid(ds['lat'].values, ds['lon'].values)
    positions = np.column_stack((lon_grid.ravel(), lat_grid.ravel()))
    wind_values = avg_wind_speed.ravel()
    def objective(locations, args):
        n_turbines = args[0]
        locations = locations.reshape(n_turbines, 2)
        total_wind = 0
        for loc in locations:
            idx = np.argmin(np.linalg.norm(positions - loc, axis=1))
            total_wind += wind_values[idx]
        for i in range(n_turbines):
            for j in range(i+1, n_turbines):
                dist = np.linalg.norm(locations[i] - locations[j]) * 111000
                if dist < 0.5:
                    total_wind -= 1000
        return -total_wind
    bounds = [(25.3, 25.9), (-34.2, -33.6)] * NUM_TURBINES
    result = differential_evolution(objective, bounds, args=[NUM_TURBINES], popsize=15, maxiter=50, workers=1, seed=seed)
    optimized_locations = result.x.reshape(NUM_TURBINES, 2)
    features = []
    for lon, lat in optimized_locations:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"blade_radius": np.random.uniform(50, 70)}
        })
    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        gdf.to_file(f.name, driver="GeoJSON")
        return f.name