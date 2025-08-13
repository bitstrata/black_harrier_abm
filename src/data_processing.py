import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import xarray as xr
from sklearn.cluster import DBSCAN
from shapely.geometry import Point

# Process GPS Data for Markov Transitions
def process_gps_data(gps_file):
    gps_df = pd.read_csv(gps_file, parse_dates=['timestamp'])
    gps_df = gps_df[gps_df['speed'] < 20]  # Remove outliers
    geometry = [Point(xy) for xy in zip(gps_df['lon'], gps_df['lat'])]
    gps_gdf = gpd.GeoDataFrame(gps_df, geometry=geometry, crs="EPSG:4326")
   
    # Cluster waypoints using DBSCAN
    coords = np.array([[p.x, p.y] for p in gps_gdf.geometry])
    db = DBSCAN(eps=0.01, min_samples=5).fit(coords)
    gps_gdf['cluster'] = db.labels_
    waypoints = gps_gdf[gps_gdf['cluster'] != -1].groupby('cluster').agg({
        'geometry': lambda x: Point(x.x.mean(), x.y.mean()),
        'alt': 'mean'
    }).reset_index()
   
    # Calculate Markov transition probabilities
    transitions = {}
    for harrier_id in gps_gdf['harrier_id'].unique():
        harrier_data = gps_gdf[gps_gdf['harrier_id'] == harrier_id].sort_values('timestamp')
        for i in range(len(harrier_data) - 1):
            c1, c2 = harrier_data['cluster'].iloc[i], harrier_data['cluster'].iloc[i + 1]
            month = harrier_data['timestamp'].iloc[i].month
            if c1 != -1 and c2 != -1:
                key = (month, c1, c2)
                transitions[key] = transitions.get(key, 0) + 1
    transition_probs = {}
    for month in range(1, 13):
        month_trans = {k: v for k, v in transitions.items() if k[0] == month}
        total = sum(month_trans.values())
        if total > 0:
            for k in month_trans:
                transition_probs[k] = month_trans[k] / total
   
    # Agent data
    agents = gps_gdf.groupby('harrier_id').agg({
        'geometry': lambda x: list(x),
        'alt': 'mean',
        'speed': 'mean'
    }).reset_index()
    agents['initial_pos'] = agents['geometry'].apply(lambda x: x[0])
    return waypoints, agents, transition_probs

# Process LiDAR Data
def process_lidar_data(lidar_file):
    dem = gpd.read_file(lidar_file).to_crs("EPSG:4326")
    dem['slope'] = dem['elevation'].apply(lambda x: np.gradient(x)[0] if len(x) > 1 else 0)
    nodes = dem[dem['slope'] > 5][['geometry', 'elevation', 'slope']]
    return nodes

# Process Weather Data
def process_weather_data(weather_file):
    weather = xr.open_dataset(weather_file)
    weather['thermal'] = weather['wind_speed'] * (1000 / weather['pressure'])
    thermal_data = weather[['thermal', 'wind_speed']].to_dataframe().reset_index()
    thermal_data['turbine_active'] = thermal_data['wind_speed'] > WIND_THRESHOLD
    return thermal_data

# Process Turbine Data
def process_turbine_data(turbine_file):
    turbines = gpd.read_file(turbine_file).to_crs("EPSG:4326")
    turbines['collision_zone'] = turbines.geometry.buffer(turbines['blade_radius'] + 50 / 111000)
    return turbines

# Build Dynamic Graph
def build_graph(waypoints, nodes, turbines, thermal_data):
    G = nx.Graph()
    for idx, row in waypoints.iterrows():
        G.add_node(idx, pos=(row.geometry.x, row.geometry.y), elevation=row['alt'], type='waypoint')
    for idx, row in nodes.iterrows():
        G.add_node(idx + len(waypoints), pos=(row.geometry.x, row.geometry.y),
                   elevation=row['elevation'], slope=row['slope'], type='terrain')
    for idx, row in turbines.iterrows():
        G.add_node(idx + len(waypoints) + len(nodes), pos=(row.geometry.x, row.geometry.y),
                   type='turbine', collision_zone=row['collision_zone'])
    for n1 in G.nodes:
        for n2 in G.nodes:
            if n1 < n2:
                p1 = Point(G.nodes[n1]['pos'])
                p2 = Point(G.nodes[n2]['pos'])
                dist = p1.distance(p2) * 111000
                if dist < 10000:
                    risk = 0.3 if any(p1.within(t['collision_zone']) or p2.within(t['collision_zone'])
                                    for _, t in turbines.iterrows()) else 0
                    G.add_edge(n1, n2, distance=dist, turbine_risk=risk, thermal=thermal_data['thermal'].mean(),
                               turbine_active=thermal_data['turbine_active'].mean())
    return G