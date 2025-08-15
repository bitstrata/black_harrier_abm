from typing import Tuple
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import rasterio
from rasterio.transform import xy
from rasterio.crs import CRS
from pyproj import Transformer

def aoi_bounds_to_utm(lat_min: float, lat_max: float, lon_min: float, lon_max: float, epsg: int) -> Tuple[float,float,float,float,CRS]:
    utm = CRS.from_epsg(epsg)
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    corners = [(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_min), (lon_max, lat_max)]
    xs, ys = zip(*[to_utm.transform(LON, LAT) for (LON, LAT) in corners])
    return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys)), utm

def raster_centers_to_wgs84(src: rasterio.io.DatasetReader) -> tuple[np.ndarray, np.ndarray]:
    rows = np.arange(src.height); cols = np.arange(src.width)
    cc, rr = np.meshgrid(cols, rows)
    xs, ys = xy(src.transform, rr, cc, offset="center")
    xs = np.asarray(xs); ys = np.asarray(ys)
    if src.crs and src.crs.is_projected:
        to_ll = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
        lons, lats = to_ll.transform(xs, ys)
    else:
        lons, lats = xs, ys
    return lons, lats

def raster_to_geojson_points(path: str) -> str:
    import tempfile
    with rasterio.open(path) as src:
        elev = src.read(1); slope = src.read(2)
        lons, lats = raster_centers_to_wgs84(src)
    geoms = [Point(lon, lat) for lon, lat in zip(lons.ravel(), lats.ravel())]
    gdf = gpd.GeoDataFrame({"elevation": elev.ravel().astype(float),
                            "slope": slope.ravel().astype(float)},
                           geometry=geoms, crs="EPSG:4326")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
        gdf.to_file(f.name, driver="GeoJSON")
        return f.name
