from __future__ import annotations
from .weather_io import read_dem_grid
from .weather_core import build_weather_dataset, write_weather_netcdf

def generate_weather_nc(lidar_file: str, seed: int) -> str:
    """
    Public API: read DEM (GeoJSON or GeoTIFF), synthesize weather, return NetCDF path.
    """
    lat_axis, lon_axis, elevation_grid, slope_grid = read_dem_grid(lidar_file)
    ds = build_weather_dataset(lat_axis, lon_axis, elevation_grid, slope_grid, seed)
    return write_weather_netcdf(ds)
