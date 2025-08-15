from typing import Tuple
import numpy as np
from numba import njit, prange

@njit(parallel=True, fastmath=True)
def perlin_noise_2d(x_points: int, y_points: int, scale: float = 10.0,
                    octaves: int = 6, persistence: float = 0.5,
                    lacunarity: float = 2.0, seed: int = 0) -> np.ndarray:
    np.random.seed(seed)
    total = np.zeros((x_points, y_points), dtype=np.float64)
    frequency = 1.0
    amplitude = 1.0
    max_value = 0.0
    for _ in range(octaves):
        freq = frequency * scale
        amp = amplitude
        gx = np.random.rand(x_points + 1, y_points + 1) * 2 - 1
        gy = np.random.rand(x_points + 1, y_points + 1) * 2 - 1
        for i in prange(x_points):
            for j in prange(y_points):
                xf = i / freq; yf = j / freq
                x0 = int(xf); y0 = int(yf); x1 = x0 + 1; y1 = y0 + 1
                sx = xf - x0; sy = yf - y0
                n0 = gx[x0 % (x_points+1), y0 % (y_points+1)] * sx + gy[x0 % (x_points+1), y0 % (y_points+1)] * sy
                n1 = gx[x1 % (x_points+1), y0 % (y_points+1)] * (sx-1) + gy[x1 % (x_points+1), y0 % (y_points+1)] * sy
                ix0 = n0 + sx * (n1 - n0)
                n0 = gx[x0 % (x_points+1), y1 % (y_points+1)] * sx + gy[x0 % (x_points+1), y1 % (y_points+1)] * (sy-1)
                n1 = gx[x1 % (x_points+1), y1 % (y_points+1)] * (sx-1) + gy[x1 % (x_points+1), y1 % (y_points+1)] * (sy-1)
                ix1 = n0 + sx * (n1 - n0)
                total[i, j] += (ix0 + sy * (ix1 - ix0)) * amp
        max_value += amp
        amplitude *= persistence
        frequency *= lacunarity
    return total / max_value

@njit(parallel=True, cache=True, fastmath=True)
def slope_degrees_from_dem_m(elev: np.ndarray, dx_m: float, dy_m: float) -> np.ndarray:
    h, w = elev.shape
    out = np.zeros((h, w), dtype=np.float32)
    for i in prange(h):
        for j in range(w):
            if j == 0:   dzdx = (elev[i, j+1] - elev[i, j]) / dx_m
            elif j == w-1: dzdx = (elev[i, j] - elev[i, j-1]) / dx_m
            else:        dzdx = (elev[i, j+1] - elev[i, j-1]) / (2.0*dx_m)
            if i == 0:   dzdy = (elev[i+1, j] - elev[i, j]) / dy_m
            elif i == h-1: dzdy = (elev[i, j] - elev[i-1, j]) / dy_m
            else:        dzdy = (elev[i+1, j] - elev[i-1, j]) / (2.0*dy_m)
            out[i, j] = np.degrees(np.arctan(np.sqrt(dzdx*dzdx + dzdy*dzdy)))
    return out

def utm_epsg_from_lonlat(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 + zone) if lat >= 0 else (32700 + zone)
