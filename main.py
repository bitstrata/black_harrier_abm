import pandas as pd
import numpy as np
import random
import os
from src.models import HarrierModel
from src.visualization import HarrierVisualization
from data.generate_harrier_gps import generate_harrier_gps
from data.generate_lidar_dem import generate_lidar_dem
from data.generate_weather_nc import generate_weather_nc
from data.optimize_turbine_placement import optimize_turbine_placement

def run_simulation(years=100, seed=42):
    # Set pseudo-random seed for repeatability
    np.random.seed(seed)
    random.seed(seed)
    
    # Generate temporary data files
    gps_file = generate_harrier_gps(seed)
    lidar_file = generate_lidar_dem(seed)
    weather_file = generate_weather_nc(lidar_file, seed)
    turbine_file = optimize_turbine_placement(weather_file, seed)
    
    # Run model
    model = HarrierModel(gps_file, lidar_file, weather_file, turbine_file)
    for _ in range(years * 12):
        model.step()
        if _ % 12 == 0:
            HarrierVisualization(model)
    
    # Collect results
    data = model.datacollector.get_model_vars_dataframe()
    curtailment = {f"Turbine_{i}": times for i, (t, times) in enumerate(model.curtailment_schedule.items())}
    curtailment_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in curtailment.items()]))
    
    # Clean up temporary files
    for f in [gps_file, lidar_file, weather_file, turbine_file]:
        try:
            os.unlink(f)
        except OSError:
            pass
    
    return data, curtailment_df

if __name__ == "__main__":
    data, curtailment = run_simulation()
    print(f"Final Population: {data['Population'].iloc[-1]}")
    print(f"Average Annual Fatalities: {data['Fatalities'].mean() * 12}")
    print(f"Updated Collision Probability: {data['Collision_Prob'].iloc[-1]:.3f}")
    if data['Fatalities'].mean() * 12 >= 3:
        print("Warning: Population may collapse in ~100 years with 3 fatalities/year")
    if data['Fatalities'].mean() * 12 >= 5:
        print("Warning: Population may collapse in ~75 years with 5 fatalities/year")
    print("Curtailment Recommendations (Month, Hour):")
    print(curtailment)
    data.to_csv("simulation_results.csv")
    curtailment.to_csv("curtailment_schedule.csv")