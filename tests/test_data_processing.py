import pytest
from src.data_processing import process_gps_data

def test_process_gps_data():
    # Use a sample GPS file or mock data
    waypoints, agents, transition_probs = process_gps_data("data/harrier_gps.csv")
    assert not waypoints.empty
    assert not agents.empty
    assert len(transition_probs) > 0