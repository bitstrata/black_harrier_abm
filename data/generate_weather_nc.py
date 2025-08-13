import xarray as xr
import pandas as pd
import numpy as np

# Generate dummy weather data
times = pd.date_range("2023-01-01", "2023-12-31 23:00:00", freq="H")
wind_speed = np.random.uniform(0, 10, len(times))
pressure = np.random.uniform(900, 1100, len(times))
thermal = wind_speed * 1000 / pressure
turbine_active = wind_speed > 3

ds = xr.Dataset(
    {
        "wind_speed": (["time"], wind_speed),
        "pressure": (["time"], pressure),
        "thermal": (["time"], thermal),
        "turbine_active": (["time"], turbine_active)
    },
    coords={"time": times}
)
ds.to_netcdf("data/weather.nc")