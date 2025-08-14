import geopandas as gpd
import numpy as np
import noise
import tempfile
from shapely.geometry import Point

def generate_lidar_dem(seed):
    np.random.seed(seed)

    # Grid parameters
    n_points = 100
    lat_min, lat_max = -34.2, -33.6
    lon_min, lon_max = 25.3, 25.9
    lats = np.linspace(lat_min, lat_max, n_points)
    lons = np.linspace(lon_min, lon_max, n_points)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Vectorized base elevation
    base_elevation = 50 + (lat_grid - lat_min) / (lat_max - lat_min) * 250

    # Vectorized Perlin noise (still loop over axes but much faster than i/j loops)
    noise_grid = np.array([
        [noise.pnoise2(i / 10.0, j / 10.0, octaves=6, persistence=0.5, lacunarity=2.0)
         for j in range(n_points)]
        for i in range(n_points)
    ])

    # Combine base + noise, clip to realistic range
    elevations = np.clip(base_elevation + noise_grid * 150, 0, 500)

    # Calculate slope (degrees)
    dy, dx = np.gradient(elevations,
                         (lat_max - lat_min) / n_points,
                         (lon_max - lon_min) / n_points)
    slopes = np.clip(np.degrees(np.sqrt(dx**2 + dy**2)), 0, 15)

    # Flatten arrays for GeoDataFrame
    coords = [Point(lon, lat) for lon, lat in zip(lon_grid.ravel(), lat_grid.ravel())]
    gdf = gpd.GeoDataFrame({
        "elevation": elevations.ravel(),
        "slope": slopes.ravel()
    }, geometry=coords, crs="EPSG:4326")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        gdf.to_file(f.name, driver="GeoJSON")
        return f.name
