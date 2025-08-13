import geopandas as gpd
import numpy as np
import noise
import tempfile

def generate_lidar_dem(seed):
    np.random.seed(seed)
    n_points = 100
    lat_min, lat_max = -34.2, -33.6
    lon_min, lon_max = 25.3, 25.9
    lat = np.linspace(lat_min, lat_max, n_points)
    lon = np.linspace(lon_min, lon_max, n_points)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    elevations = np.zeros((n_points, n_points))
    for i in range(n_points):
        for j in range(n_points):
            base_elevation = 50 + (lat[i] - lat_min) / (lat_max - lat_min) * 250
            noise_value = noise.pnoise2(i / 10.0, j / 10.0, octaves=6, persistence=0.5, lacunarity=2.0)
            elevation = base_elevation + noise_value * 150
            elevations[i, j] = np.clip(elevation, 0, 500)
    dy, dx = np.gradient(elevations, (lat_max - lat_min) / n_points, (lon_max - lon_min) / n_points)
    slopes = np.degrees(np.sqrt(dx**2 + dy**2))
    slopes = np.clip(slopes, 0, 15)
    features = []
    for i in range(n_points):
        for j in range(n_points):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon_grid[i, j], lat_grid[i, j]]},
                "properties": {"elevation": float(elevations[i, j]), "slope": float(slopes[i, j])}
            })
    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        gdf.to_file(f.name, driver="GeoJSON")
        return f.name