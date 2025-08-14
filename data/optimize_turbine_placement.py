import numpy as np
from joblib import Parallel, delayed
from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution
import src.config as config

# Precompute turbine power curve interpolator
power_curve_speeds, power_curve_output = zip(*config.TURBINE_POWER_CURVE)
power_fn = interp1d(power_curve_speeds, power_curve_output,
                    kind='linear', bounds_error=False, fill_value=0.0)

def simulate_layout_energy(layout_coords, wind_data, lat_grid, lon_grid):
    """
    Compute total annual energy (kWh) for given turbine coordinates.

    layout_coords: flat list [lat1, lon1, lat2, lon2, ...]
    wind_data: xarray.DataArray with dims [time, lat, lon]
    lat_grid, lon_grid: arrays for spatial indexing
    """
    total_energy = 0.0

    for i in range(0, len(layout_coords), 2):
        lat, lon = layout_coords[i], layout_coords[i+1]

        # Find nearest grid cell
        lat_idx = np.abs(lat_grid - lat).argmin()
        lon_idx = np.abs(lon_grid - lon).argmin()

        # Extract wind speed time series
        wind_ts = wind_data[:, lat_idx, lon_idx].values

        # Convert wind speed → kW
        power_ts = power_fn(wind_ts)  # kW at each hour

        # Sum over all hours (convert kW·h to MWh if desired)
        total_energy += power_ts.sum()

    return -total_energy  # Negative for minimization

def optimize_turbine_placement(wind_data, num_turbines=10, bounds=None, workers=-1):
    """
    Optimize turbine placement to maximize annual energy production.

    wind_data: xarray.DataArray [time, lat, lon]
    bounds: list of (min, max) tuples for lat/lon
    workers: -1 for all CPUs
    """
    lat_grid = wind_data.lat.values
    lon_grid = wind_data.lon.values

    if bounds is None:
        lat_min, lat_max = lat_grid.min(), lat_grid.max()
        lon_min, lon_max = lon_grid.min(), lon_grid.max()
        bounds = [(lat_min, lat_max), (lon_min, lon_max)] * num_turbines

    result = differential_evolution(
        simulate_layout_energy,
        bounds,
        args=(wind_data, lat_grid, lon_grid),
        strategy='best1bin',
        maxiter=100,
        popsize=15,
        tol=0.01,
        mutation=(0.5, 1),
        recombination=0.7,
        polish=True,
        workers=workers,
        updating='deferred'  # Necessary for parallelization
    )

    return result