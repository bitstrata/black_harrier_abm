import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os

import geopandas as gpd
import rasterio
from rasterio.crs import CRS
from rasterio.transform import rowcol
from pyproj import Transformer

from src.config import BREEDING_MONTHS


def _build_dem_sampler(dem_path):
    """
    Build a fast sampler for elevation (m) and slope (deg) for either:
      - GeoTIFF (preferred): band 1 = elevation (m), band 2 = slope (deg, optional)
      - GeoJSON (square grid) with 'elevation' and 'slope' fields.
    Returns a tuple: (sampler_fn, metadata_dict)
      sampler_fn(lat, lon) -> (elev_m, slope_deg)
    """
    ext = os.path.splitext(dem_path)[1].lower()

    if ext in (".tif", ".tiff"):
        src = rasterio.open(dem_path)
        elev = src.read(1)  # (rows, cols)
        slope = src.read(2) if src.count >= 2 else None
        crs = src.crs
        transform = src.transform

        # If slope band is missing, approximate via numeric gradient (meters)
        if slope is None:
            dx = abs(transform.a)
            dy = abs(transform.e)
            gy, gx = np.gradient(elev.astype(np.float64), dy, dx)
            slope = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy))).astype(np.float32)

        # Prepare transformer to dataset CRS (likely UTM)
        to_src = None
        if crs and CRS.from_user_input(crs).is_projected:
            to_src = Transformer.from_crs("EPSG:4326", crs, always_xy=True)

        n_rows, n_cols = elev.shape

        def sample_fn(lat, lon):
            # Transform lon/lat -> dataset CRS if needed
            if to_src is not None:
                x, y = to_src.transform(lon, lat)
            else:
                x, y = lon, lat
            # Convert map coords -> row/col (nearest)
            r, c = rowcol(transform, x, y, op=round)
            if r < 0 or r >= n_rows or c < 0 or c >= n_cols:
                return np.nan, np.nan
            return float(elev[r, c]), float(slope[r, c])

        return sample_fn, {"type": "raster", "crs": crs, "transform": transform, "shape": elev.shape, "src": src}

    # GeoJSON fallback (square grid)
    dem = gpd.read_file(dem_path)
    lat = np.array([p.y for p in dem.geometry], dtype=np.float64)
    lon = np.array([p.x for p in dem.geometry], dtype=np.float64)
    elevation = dem["elevation"].values.astype(np.float32)
    slope = dem["slope"].values.astype(np.float32)

    n = int(np.sqrt(len(lat)))
    if n * n != len(lat):
        raise ValueError("GeoJSON DEM must be a square grid of points.")

    lat_grid = lat.reshape((n, n))
    lon_grid = lon.reshape((n, n))
    elev_grid = elevation.reshape((n, n))
    slope_grid = slope.reshape((n, n))

    # Build monotonically increasing axes
    lat_axis = np.unique(np.round(lat_grid[:, 0], 12)).astype(np.float64)
    lon_axis = np.unique(np.round(lon_grid[0, :], 12)).astype(np.float64)
    # Ensure ascending axes and flip arrays if needed
    if lat_axis[0] > lat_axis[-1]:
        lat_axis = lat_axis[::-1].copy()
        elev_grid = elev_grid[::-1, :]
        slope_grid = slope_grid[::-1, :]
    if lon_axis[0] > lon_axis[-1]:
        lon_axis = lon_axis[::-1].copy()
        elev_grid = elev_grid[:, ::-1]
        slope_grid = slope_grid[:, ::-1]

    def _nearest_index(axis, value):
        idx = np.searchsorted(axis, value)
        if idx <= 0:
            return 0
        if idx >= len(axis):
            return len(axis) - 1
        # pick closest neighbor
        return idx if (axis[idx] - value) < (value - axis[idx - 1]) else idx - 1

    def sample_fn(lat, lon):
        i = _nearest_index(lat_axis, lat)
        j = _nearest_index(lon_axis, lon)
        return float(elev_grid[i, j]), float(slope_grid[i, j])

    return sample_fn, {"type": "geojson", "lat_axis": lat_axis, "lon_axis": lon_axis}


def generate_harrier_gps(seed=42, num_harriers=10, points_per_harrier=1500, dem_path=None):
    """
    Generate synthetic GPS tracks for harriers, simulating breeding and non-breeding behavior.

    If dem_path is provided (GeoTIFF or GeoJSON), the generator will:
      - sample terrain elevation (m) and slope (deg) at each point,
      - assign altitude AGL and compute ASL = elev + AGL,
      - reduce roaming step sizes in steeper terrain.

    Returns:
        Path to CSV file containing simulated GPS data.
    """
    np.random.seed(seed)

    # Constants (AOI bounds)
    START_DATE = datetime(2023, 1, 1)
    LAT_MIN, LAT_MAX = -34.2, -33.6
    LON_MIN, LON_MAX = 25.3, 25.9
    NEST_LOCATIONS = [(-33.920, 25.620), (-33.880, 25.580)]

    # Optional DEM sampler
    sampler = None
    if dem_path is not None:
        sampler, _meta = _build_dem_sampler(dem_path)

    rows = []

    for harrier_id in range(1, num_harriers + 1):
        current_time = START_DATE
        # Start position anywhere in AOI
        current_pos = np.random.uniform([LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX])

        for _ in range(points_per_harrier):
            month = current_time.month

            # --- Movement model ---
            if month in BREEDING_MONTHS:
                # Stay close to nest in breeding months
                nest_lat, nest_lon = NEST_LOCATIONS[np.random.randint(len(NEST_LOCATIONS))]
                # small Gaussian around nest
                lat = np.random.normal(nest_lat, 0.005)
                lon = np.random.normal(nest_lon, 0.005)
                # Clip to AOI
                lat = float(np.clip(lat, LAT_MIN, LAT_MAX))
                lon = float(np.clip(lon, LON_MIN, LON_MAX))

                # Base flight parameters (breeding lower, slower)
                base_speed = np.random.uniform(2, 8)
                alt_agl = np.random.uniform(20, 50)
            else:
                # Roaming step from current position
                # Step size scaled by slope (computed at current position if DEM available)
                if sampler is not None:
                    elev_here, slope_here = sampler(current_pos[0], current_pos[1])
                    slope_here = 0.0 if np.isnan(slope_here) else slope_here
                    # shrink step up to -60% by 20° slope
                    step_scale = 1.0 - min(slope_here, 20.0) / 20.0 * 0.6
                else:
                    step_scale = 1.0

                # Random small move in lat/lon degrees (AOI sized ~0.6° each axis)
                dlat = np.random.uniform(-0.01, 0.01) * step_scale
                dlon = np.random.uniform(-0.01, 0.01) * step_scale
                lat = float(np.clip(current_pos[0] + dlat, LAT_MIN, LAT_MAX))
                lon = float(np.clip(current_pos[1] + dlon, LON_MIN, LON_MAX))

                # Base flight parameters (non-breeding higher, faster)
                base_speed = np.random.uniform(5, 15)
                alt_agl = np.random.uniform(60, 100)

            # --- Terrain sampling ---
            if sampler is not None:
                elev_m, slope_deg = sampler(lat, lon)
                if np.isnan(elev_m):
                    # fallback if outside coverage
                    elev_m, slope_deg = 0.0, 0.0
            else:
                elev_m, slope_deg = 0.0, 0.0  # flat world fallback

            # Slope-aware speed reduction (up to -50% by 20° slope)
            speed = base_speed * (1.0 - min(max(slope_deg, 0.0), 20.0) / 20.0 * 0.5)
            speed = max(speed, 0.1)

            # Convert to ASL altitude if DEM available
            alt_asl = elev_m + alt_agl

            # Record
            rows.append((
                harrier_id,
                current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                lat, lon,
                alt_asl,   # keep 'alt' column as ASL for compatibility
                speed,
                elev_m,    # extra columns (useful for modeling)
                slope_deg,
                alt_agl
            ))

            # Advance state/time
            current_pos = (lat, lon)
            # 1–2 hours between points, as before
            current_time += timedelta(hours=np.random.randint(1, 3))

    # DataFrame with backward-compatible columns + extras
    df = pd.DataFrame(
        rows,
        columns=[
            'harrier_id', 'timestamp', 'lat', 'lon',
            'alt', 'speed',            # original columns (alt now ASL if DEM is used)
            'elev_m', 'slope_deg',     # new: sampled terrain
            'alt_agl'                  # new: AGL component used to form ASL
        ]
    )

    # Write to a temporary CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name
