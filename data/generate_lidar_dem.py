from typing import Optional, Tuple
import rasterio

from .terrain import build_dem_geotiff
from .conversions import raster_to_geojson_points
from .utils import slope_degrees_from_dem_m  # used if we add slope to a real DEM

def generate_lidar_dem_geotiff(
    seed: int,
    n_x: int = 100, n_y: int = 100,
    lat_min: float = -34.2, lat_max: float = -33.6,
    lon_min: float = 25.3,  lon_max: float = 25.9,
    feature_scale_m: float = 1200.0,
    octaves: int = 6, persistence: float = 0.5, lacunarity: float = 2.0,
    base_min: float = 50.0, base_span: float = 250.0,
    noise_amplitude: float = 150.0,
    elev_clip: Tuple[float, float] = (0.0, 500.0),
    source_path: Optional[str] = None,
    compute_slope_if_missing: bool = True,
) -> str:
    """
    Returns path to a 2-band GeoTIFF (Band1=elevation_m, Band2=slope_deg), UTM CRS.
    If source_path is provided (real DEM), return it if it already has slope; else compute slope & write a 2-band copy.
    """
    if source_path:
        with rasterio.open(source_path) as src:
            if src.count >= 2:
                return source_path
            elev = src.read(1)
            dx = abs(src.transform.a); dy = abs(src.transform.e)
            slope = slope_degrees_from_dem_m(elev.astype("float64"), dx, dy).astype("float32")
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
                out = f.name
            prof = src.profile.copy(); prof.update(count=2, dtype="float32", compress="deflate",
                                                   tiled=True, interleave="pixel")
            with rasterio.open(out, "w", **prof) as dst:
                dst.write(elev.astype("float32"), 1); dst.set_band_description(1, "elevation_m")
                dst.write(slope, 2); dst.set_band_description(2, "slope_deg")
            return out

    path, _utm = build_dem_geotiff(
        seed=seed, n_x=n_x, n_y=n_y,
        lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
        feature_scale_m=feature_scale_m,
        octaves=octaves, persistence=persistence, lacunarity=lacunarity,
        base_min=base_min, base_span=base_span,
        noise_amplitude=noise_amplitude, elev_clip=elev_clip,
    )
    return path

def generate_lidar_dem(
    seed: int,
    n_x: int = 100, n_y: int = 100,
    lat_min: float = -34.2, lat_max: float = -33.6,
    lon_min: float = 25.3,  lon_max: float = 25.9,
    feature_scale_m: float = 1200.0,
    octaves: int = 6, persistence: float = 0.5, lacunarity: float = 2.0,
    base_min: float = 50.0, base_span: float = 250.0,
    noise_amplitude: float = 150.0,
    elev_clip: Tuple[float, float] = (0.0, 500.0),
    source_path: Optional[str] = None,
) -> str:
    """
    Backward-compatible: returns a WGS84 GeoJSON sampled from a 2-band GeoTIFF.
    """
    tif = generate_lidar_dem_geotiff(
        seed=seed, n_x=n_x, n_y=n_y,
        lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
        feature_scale_m=feature_scale_m, octaves=octaves, persistence=persistence, lacunarity=lacunarity,
        base_min=base_min, base_span=base_span, noise_amplitude=noise_amplitude, elev_clip=elev_clip,
        source_path=source_path,
    )
    return raster_to_geojson_points(tif)
