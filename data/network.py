"""
SmartRoute – Road Network Data Loader & Graph Representation
Provides beginner-friendly helper functions to load the road network JSON,
manage road traffic overrides, build graph adjacency lists, and compute distances.
"""

import json
import math
import os

# Path to the road_network.json file
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
NETWORK_JSON_PATH = os.path.join(DATA_DIR, "road_network.json")


def load_network_data(filepath=NETWORK_JSON_PATH):
    """Loads and returns the raw JSON dictionary containing intersections and roads."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_road_map(network_data):
    """Returns a lookup dictionary mapping road_id -> road object."""
    return {road["id"]: road for road in network_data.get("roads", [])}


def get_network_with_traffic(network_data, traffic_overrides=None):
    """
    Returns a copy of the network data with active travel times computed
    based on any active traffic overrides.
    """
    if traffic_overrides is None:
        traffic_overrides = {}

    roads_copy = []
    for road in network_data.get("roads", []):
        road_id = road["id"]
        base_time = float(road["travel_time"])
        current_time = float(traffic_overrides.get(road_id, base_time))
        is_modified = road_id in traffic_overrides and current_time != base_time

        roads_copy.append({
            "id": road_id,
            "from": road["from"],
            "to": road["to"],
            "name": road.get("name", f"Road {road_id}"),
            "base_travel_time": base_time,
            "current_travel_time": round(current_time, 2),
            "is_modified": is_modified,
            "bidirectional": road.get("bidirectional", True)
        })

    return {
        "city": network_data.get("city", "Tumakuru"),
        "description": network_data.get("description", ""),
        "max_speed_units_per_min": network_data.get("max_speed_units_per_min", 40.0),
        "warehouse": network_data.get("warehouse", "A"),
        "destinations": network_data.get("destinations", []),
        "intersections": network_data.get("intersections", {}),
        "roads": roads_copy,
        "active_traffic_overrides": traffic_overrides
    }


def build_adjacency_list(network_data, traffic_overrides=None):
    """
    Builds a bidirectional graph represented as an adjacency list.
    
    Structure:
    {
        "A": [{"neighbor": "B", "cost": 5.0, "road_id": "A-B"}, ...],
        "B": [{"neighbor": "A", "cost": 5.0, "road_id": "A-B"}, ...],
        ...
    }
    """
    if traffic_overrides is None:
        traffic_overrides = {}

    intersections = network_data["intersections"]
    roads = network_data["roads"]

    # Initialize empty neighbor list for each intersection
    adj = {node: [] for node in intersections.keys()}

    for road in roads:
        road_id = road["id"]
        u = road["from"]
        v = road["to"]

        # Use updated travel time if traffic override exists, else base travel_time
        base_cost = road.get("current_travel_time", road.get("travel_time", 1.0))
        cost = float(traffic_overrides.get(road_id, base_cost))

        # Add forward edge
        adj[u].append({
            "neighbor": v,
            "cost": cost,
            "road_id": road_id
        })

        # Add reverse edge if bidirectional
        if road.get("bidirectional", True):
            adj[v].append({
                "neighbor": u,
                "cost": cost,
                "road_id": road_id
            })

    return adj


def get_straight_line_distance(node_a, node_b, intersections):
    """Calculates Euclidean straight-line distance: sqrt((x2 - x1)^2 + (y2 - y1)^2)"""
    pos_a = intersections[node_a]
    pos_b = intersections[node_b]
    return math.hypot(pos_b["x"] - pos_a["x"], pos_b["y"] - pos_a["y"])
