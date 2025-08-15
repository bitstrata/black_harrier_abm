from typing import Optional, Tuple
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

from .utils import perlin_noise_2d, slope_degrees_from_dem_m, utm_epsg_from_lonlat
from .conversions import aoi_bounds_to_utm

def build_dem_geotiff(
    seed: int,
    n_x: int, n_y: int,
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    feature_scale_m: float,
    octaves: int, persistence: float, lacunarity: float,
    base_min: float, base_span: float,
    noise_amplitude: float,
    elev_clip: Tuple[float, float],
) -> tuple[str, CRS]:
    import tempfile
    lon_c = 0.5*(lon_min + lon_max); lat_c = 0.5*(lat_min + lat_max)
    epsg = utm_epsg_from_lonlat(lon_c, lat_c)
    x_min, y_min, x_max, y_max, utm = aoi_bounds_to_utm(lat_min, lat_max, lon_min, lon_max, epsg)

    dx = (x_max - x_min) / (n_x - 1); dy = (y_max - y_min) / (n_y - 1)
    scale_px = max(feature_scale_m / max(min(dx, dy), 1e-9), 1.0)

    # perlin returns (n_x, n_y) — transpose to (n_y, n_x)
    noise_xy = perlin_noise_2d(n_x, n_y, scale=scale_px,
                               octaves=octaves, persistence=persistence,
                               lacunarity=lacunarity, seed=seed)
    noise = noise_xy.T

    y_norm = (np.arange(n_y, dtype=np.float64) * dy) / max((y_max - y_min), 1e-9)
    base = base_min + y_norm[:, None] * base_span
    elev = np.clip(base + noise * noise_amplitude, elev_clip[0], elev_clip[1]).astype(np.float32)

    slope = slope_degrees_from_dem_m(elev.astype(np.float64), float(dx), float(dy)).astype(np.float32)

    transform = from_bounds(x_min, y_min, x_max, y_max, n_x, n_y)
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        path = f.name

    profile = dict(driver="GTiff", height=n_y, width=n_x, count=2,
                   dtype="float32", crs=utm, transform=transform,
                   tiled=True, compress="deflate", interleave="pixel")

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(elev, 1); dst.set_band_description(1, "elevation_m")
        dst.write(slope, 2); dst.set_band_description(2, "slope_deg")
    return path, utm
