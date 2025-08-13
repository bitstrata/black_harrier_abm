import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
from shapely.geometry import Point as ShapelyPoint
from sklearn.cluster import DBSCAN
import xarray as xr
from src.config import FORAGING_RANGE, NON_BREEDING_RANGE, BREEDING_MONTHS, MIGRATION_MONTHS, WIND_THRESHOLD

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, other):
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def within(self, geometry):
        from shapely.geometry import Point as ShapelyPoint
        return ShapelyPoint(self.x, self.y).within(geometry)

def process_gps_data(gps_file):
    gps = pd.read_csv(gps_file)
    gps = gps[gps['speed'] < 20]
    coords = gps[['lat', 'lon']].values
    db = DBSCAN(eps=0.05, min_samples=5).fit(coords)  # Increased eps to 0.05
    gps['cluster'] = db.labels_
    waypoints = []
    for cluster in set(db.labels_):
        if cluster != -1:
            cluster_points = coords[db.labels_ == cluster]
            centroid = cluster_points.mean(axis=0)
            waypoints.append(Point(centroid[1], centroid[0]))
    if not waypoints:  # Fallback: add a single waypoint if clustering fails
        waypoints.append(Point(gps['lon'].mean(), gps['lat'].mean()))
    agents = gps.groupby('harrier_id').first().reset_index()
    agents['initial_pos'] = [Point(row['lon'], row['lat']) for _, row in agents.iterrows()]
    transition_probs = {}
    for month in range(1, 13):
        month_data = gps[gps['timestamp'].str.contains(f'-{month:02d}-')]
        for _, row in month_data.iterrows():
            start = min(waypoints, key=lambda p: Point(row['lon'], row['lat']).distance(p))
            end = min(waypoints, key=lambda p: Point(row['lon'], row['lat']).distance(p))
            transition_probs[(month, waypoints.index(start), waypoints.index(end))] = \
                transition_probs.get((month, waypoints.index(start), waypoints.index(end)), 0) + 1
        for i in range(len(waypoints)):
            total = sum(transition_probs.get((month, i, j), 0) for j in range(len(waypoints)))
            if total > 0:
                for j in range(len(waypoints)):
                    transition_probs[(month, i, j)] = transition_probs.get((month, i, j), 0) / total
    return waypoints, agents, transition_probs

def process_lidar_data(lidar_file):
    dem = gpd.read_file(lidar_file).to_crs("EPSG:4326")
    nodes = dem[dem['slope'] > 5][['geometry', 'elevation', 'slope']]
    return nodes

def process_weather_data(weather_file):
    weather = xr.open_dataset(weather_file)
    weather['thermal'] = weather['wind_speed'] * 1000 / weather['pressure']
    weather['turbine_active'] = weather['wind_speed'] > WIND_THRESHOLD
    return weather

def process_turbine_data(turbine_file):
    turbines = gpd.read_file(turbine_file).to_crs("EPSG:4326")
    turbines['collision_zone'] = turbines.apply(
        lambda row: row['geometry'].buffer(row['blade_radius'] + 50/111000), axis=1)
    return turbines

def build_graph(waypoints, nodes, turbines, weather):
    G = nx.Graph()
    for i, point in enumerate(waypoints):
        G.add_node(i, pos=(point.x, point.y))
    for i, row in nodes.iterrows():
        G.add_node(len(waypoints) + i, pos=(row['geometry'].x, row['geometry'].y), elevation=row['elevation'])
    for i in G.nodes:
        for j in G.nodes:
            if i < j:
                dist = Point(G.nodes[i]['pos'][0], G.nodes[i]['pos'][1]).distance(
                    Point(G.nodes[j]['pos'][0], G.nodes[j]['pos'][1]))
                if dist < (FORAGING_RANGE if i < len(waypoints) else NON_BREEDING_RANGE):
                    turbine_risk = 0
                    for _, turbine in turbines.iterrows():
                        if turbine['geometry'].distance(ShapelyPoint(G.nodes[i]['pos'])) < turbine['collision_zone'].area:
                            turbine_risk += 0.15
                    thermal = weather['thermal'].mean().item()
                    G.add_edge(i, j, weight=dist, turbine_risk=turbine_risk, thermal=thermal,
                               turbine_active=weather['turbine_active'].mean().item() > 0.5)
    return G