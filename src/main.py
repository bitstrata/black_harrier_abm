from src.models import HarrierModel
from src.data_processing import GRID_SIZE, NUM_TURBINES
from src.visualization import HarrierVisualization

# Run Simulation with Visualization
def run_simulation(years=100, gps_file="data/harrier_gps.csv", lidar_file="data/lidar_dem.geojson",
                   weather_file="data/weather.nc", turbine_file="data/turbines.geojson"):
    model = HarrierModel(gps_file, lidar_file, weather_file, turbine_file)
    for _ in range(years * 12):
        model.step()
        if _ % 12 == 0:  # Visualize annually
            HarrierVisualization(model)
    data = model.datacollector.get_model_vars_dataframe()
    curtailment = {f"Turbine_{i}": times for i, (t, times) in enumerate(model.curtailment_schedule.items())}
    curtailment_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in curtailment.items()]))
    return data, curtailment_df

# Example Usage
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