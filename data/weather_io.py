from __future__ import annotations
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import xy as transform_xy
from rasterio.crs import CRS
from pyproj import Transformer

def _coords_from_raster(src: rasterio.io.DatasetReader):
    """
    Build 1D lat/lon axes from pixel centers.
    Reprojects to WGS84 if src CRS is projected. Ensures ascending axes.
    Returns: lat_axis, lon_axis, flip_lat, flip_lon
    """
    h, w = src.height, src.width
    rows = np.arange(h)
    cols = np.arange(w)

    xs0, ys0 = transform_xy(src.transform, 0, cols)   # row=0, all cols
    xs1, ys1 = transform_xy(src.transform, rows, 0)   # col=0, all rows
    xs0 = np.array(xs0); ys0 = np.array(ys0)
    xs1 = np.array(xs1); ys1 = np.array(ys1)

    if src.crs and CRS.from_user_input(src.crs).is_projected:
        to_ll = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
        lons, _ = to_ll.transform(xs0, ys0)  # along columns
        _, lats = to_ll.transform(xs1, ys1)  # along rows
    else:
        lons, lats = xs0, ys1

    lats = np.asarray(lats, dtype=np.float64)
    lons = np.asarray(lons, dtype=np.float64)

    flip_lat = lats[0] > lats[-1]
    flip_lon = lons[0] > lons[-1]
    if flip_lat:
        lats = lats[::-1].copy()
    if flip_lon:
        lons = lons[::-1].copy()

    return lats, lons, flip_lat, flip_lon


def _compute_slope_from_elev_m(elev: np.ndarray, src: rasterio.io.DatasetReader) -> np.ndarray:
    """
    Slope (degrees) from elevation (meters) using meter spacings from affine transform.
    Uses NumPy central differences (fast, dependency-free).
    """
    dx = abs(src.transform.a)
    dy = abs(src.transform.e)
    elev = elev.astype(np.float64, copy=False)
    gy, gx = np.gradient(elev, dy, dx)  # gy: dZ/dy, gx: dZ/dx
    slope = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy))).astype(np.float32)
    return slope


def _grid_from_geotiff(path: str):
    """
    Returns lat_axis, lon_axis, elevation_grid, slope_grid (lat/lon ascending).
    Uses band 1 = elevation (m); band 2 = slope (deg) if present; otherwise computes slope.
    """
    with rasterio.open(path) as src:
        elev = src.read(1).astype(np.float32)
        slope = src.read(2).astype(np.float32) if src.count >= 2 else None

        lat_axis, lon_axis, flip_lat, flip_lon = _coords_from_raster(src)
        if slope is None:
            slope = _compute_slope_from_elev_m(elev, src)

        if flip_lat:
            elev = elev[::-1, :]
            slope = slope[::-1, :]
        if flip_lon:
            elev = elev[:, ::-1]
            slope = slope[:, ::-1]

    return lat_axis, lon_axis, elev, slope


def _grid_from_geojson(path: str):
    """
    GeoJSON of points with 'elevation' and 'slope' fields.
    Returns lat_axis, lon_axis, elevation_grid, slope_grid (lat/lon ascending).
    """
    dem = gpd.read_file(path)
    lat = np.array([p.y for p in dem.geometry], dtype=np.float64)
    lon = np.array([p.x for p in dem.geometry], dtype=np.float64)
    elevation = dem["elevation"].values.astype(np.float32)
    slope = dem["slope"].values.astype(np.float32)

    n_points = int(np.sqrt(len(lat)))
    if n_points * n_points != len(lat):
        raise ValueError("GeoJSON DEM is not a square grid.")

    lat_grid = lat.reshape((n_points, n_points))
    lon_grid = lon.reshape((n_points, n_points))
    elev_grid = elevation.reshape((n_points, n_points))
    slope_grid = slope.reshape((n_points, n_points))

    lat_axis = np.unique(np.round(lat_grid[:, 0], 12)).astype(np.float64)
    lon_axis = np.unique(np.round(lon_grid[0, :], 12)).astype(np.float64)

    flip_lat = lat_axis[0] > lat_axis[-1]
    flip_lon = lon_axis[0] > lon_axis[-1]
    if flip_lat:
        lat_axis = lat_axis[::-1].copy()
        elev_grid = elev_grid[::-1, :]
        slope_grid = slope_grid[::-1, :]
    if flip_lon:
        lon_axis = lon_axis[::-1].copy()
        elev_grid = elev_grid[:, ::-1]
        slope_grid = slope_grid[:, ::-1]

    return lat_axis, lon_axis, elev_grid, slope_grid


def read_dem_grid(lidar_file: str):
    """
    Unified loader:
      - GeoTIFF (.tif/.tiff): read bands, compute slope if missing
      - GeoJSON: reshape to grid
    Returns: lat_axis, lon_axis, elevation_grid, slope_grid
    """
    ext = os.path.splitext(lidar_file)[1].lower()
    if ext in (".tif", ".tiff"):
        return _grid_from_geotiff(lidar_file)
    return _grid_from_geojson(lidar_file)
