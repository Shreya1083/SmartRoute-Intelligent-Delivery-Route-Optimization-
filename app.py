"""
SmartRoute – Intelligent Delivery Route Optimization
Backend Flask Application

Exposes REST APIs for:
1. GET  /api/health         - Service health check
2. GET  /api/network        - Road network dataset with active travel times
3. POST /api/find-route     - A* optimal delivery path finder
4. POST /api/update-traffic - Modify travel-time cost on a road
5. POST /api/traffic/reset  - Reset all roads back to default travel times
"""

from flask import Flask, jsonify, request, render_template
from data.network import (
    load_network_data,
    build_adjacency_list,
    get_network_with_traffic,
    get_road_map
)
from backend.astar import astar_search

app = Flask(__name__)

# Base dataset
BASE_NETWORK = load_network_data()
INTERSECTIONS = BASE_NETWORK["intersections"]
MAX_SPEED = BASE_NETWORK.get("max_speed_units_per_min", 40.0)
ROAD_MAP = get_road_map(BASE_NETWORK)

# Active traffic overrides: { "road_id": float(new_travel_time) }
ACTIVE_TRAFFIC = {}


@app.after_request
def apply_cors_headers(response):
    """
    Configures CORS headers so the browser frontend can communicate
    seamlessly with this local Flask backend.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/", methods=["GET"])
def index():
    """Serves the SmartRoute single-page dashboard."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend status."""
    return jsonify({
        "status": "success",
        "message": "SmartRoute Backend is running!",
        "version": "1.0.0"
    }), 200


@app.route("/api/network", methods=["GET"])
def get_network():
    """
    Returns the complete road network:
    - intersections with (x, y) coordinates
    - roads with base and current travel times
    - warehouse starting location & delivery destinations
    - list of currently active traffic bottlenecks
    """
    active_network = get_network_with_traffic(BASE_NETWORK, ACTIVE_TRAFFIC)
    return jsonify({
        "status": "success",
        "data": active_network
    }), 200


@app.route("/api/find-route", methods=["POST"])
def find_route():
    """
    Computes the optimal delivery route using the A* Search Algorithm.
    
    Expected JSON Body:
    {
        "source": "A",
        "destination": "L",
        "traffic": { "B-E": 12.0 }   // optional per-query override
    }
    """
    # 1. Validate JSON presence
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request body must be a valid JSON object."
        }), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON format: expected a key-value dictionary."
        }), 400

    # 2. Extract and validate source & destination
    # Support both source/destination and start/goal naming
    source = data.get("source") or data.get("start")
    destination = data.get("destination") or data.get("goal")

    if not source:
        return jsonify({
            "status": "error",
            "message": "Missing required field: 'source'. Please provide a starting intersection (e.g. 'A')."
        }), 400

    if not destination:
        return jsonify({
            "status": "error",
            "message": "Missing required field: 'destination'. Please provide a target intersection (e.g. 'L')."
        }), 400

    source = str(source).strip().upper()
    destination = str(destination).strip().upper()

    if source not in INTERSECTIONS:
        return jsonify({
            "status": "error",
            "message": f"Source intersection '{source}' does not exist in the network. Valid intersections: {sorted(list(INTERSECTIONS.keys()))}"
        }), 400

    if destination not in INTERSECTIONS:
        return jsonify({
            "status": "error",
            "message": f"Destination intersection '{destination}' does not exist in the network. Valid intersections: {sorted(list(INTERSECTIONS.keys()))}"
        }), 400

    # 3. Merge active traffic with any per-query overrides
    query_traffic = data.get("traffic", {})
    merged_traffic = dict(ACTIVE_TRAFFIC)
    if isinstance(query_traffic, dict):
        for road_id, time_val in query_traffic.items():
            if road_id in ROAD_MAP:
                try:
                    merged_traffic[road_id] = float(time_val)
                except (ValueError, TypeError):
                    pass

    # 4. Build graph adjacency list
    graph = build_adjacency_list(BASE_NETWORK, merged_traffic)

    # 5. Run A* Search
    result = astar_search(
        start_node=source,
        goal_node=destination,
        intersections=INTERSECTIONS,
        adjacency_list=graph,
        max_speed=MAX_SPEED
    )

    if not result["success"]:
        return jsonify({
            "status": "error",
            "message": result.get("error", "No route could be found."),
            "explored_nodes": result.get("explored_nodes", [])
        }), 404

    # 6. Return successful response with comprehensive A* diagnostics
    return jsonify({
        "status": "success",
        "source": source,
        "destination": destination,
        "route": result["route"],
        "total_travel_time": result["total_travel_time"],
        "explored_nodes": result["explored_nodes"],
        "heuristics": result.get("heuristics", {}),
        "road_segments": result["road_segments"]
    }), 200


@app.route("/api/update-traffic", methods=["POST"])
@app.route("/api/traffic/update", methods=["POST"])
def update_traffic():
    """
    Updates the travel time cost of a road to simulate traffic or road clearing.
    
    Expected JSON Body:
    {
        "road_id": "B-E",
        "travel_time": 15.0
    }
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request body must be valid JSON."
        }), 400

    data = request.get_json()
    road_id = data.get("road_id")
    travel_time = data.get("travel_time")

    if not road_id:
        return jsonify({
            "status": "error",
            "message": "Missing required field: 'road_id'. Valid road IDs include: " + ", ".join(list(ROAD_MAP.keys())[:6]) + "..."
        }), 400

    if road_id not in ROAD_MAP:
        return jsonify({
            "status": "error",
            "message": f"Road ID '{road_id}' does not exist. Available road IDs: {sorted(list(ROAD_MAP.keys()))}"
        }), 400

    if travel_time is None:
        return jsonify({
            "status": "error",
            "message": "Missing required field: 'travel_time'."
        }), 400

    try:
        travel_time = float(travel_time)
        if travel_time <= 0:
            return jsonify({
                "status": "error",
                "message": "Travel time must be a positive number greater than 0."
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": f"Invalid travel_time value: '{travel_time}'. Must be a valid positive number."
        }), 400

    # Apply override
    ACTIVE_TRAFFIC[road_id] = round(travel_time, 2)
    road_info = ROAD_MAP[road_id]

    return jsonify({
        "status": "success",
        "message": f"Traffic updated on road {road_id}.",
        "road": {
            "id": road_id,
            "name": road_info.get("name"),
            "from": road_info["from"],
            "to": road_info["to"],
            "base_travel_time": road_info["travel_time"],
            "current_travel_time": ACTIVE_TRAFFIC[road_id]
        }
    }), 200


@app.route("/api/traffic/reset", methods=["POST"])
def reset_traffic():
    """Resets all road travel times back to their base values."""
    ACTIVE_TRAFFIC.clear()
    return jsonify({
        "status": "success",
        "message": "All road travel times have been reset to default values."
    }), 200


# Backward compatibility for GET /api/route tested in Phase 2
@app.route("/api/route", methods=["GET"])
def route_compat():
    """Convenience GET endpoint: /api/route?start=A&goal=L"""
    start = request.args.get("start") or request.args.get("source")
    goal = request.args.get("goal") or request.args.get("destination")
    if not start or not goal:
        return jsonify({"status": "error", "message": "Specify 'start' and 'goal' query parameters."}), 400

    graph = build_adjacency_list(BASE_NETWORK, ACTIVE_TRAFFIC)
    res = astar_search(start.upper(), goal.upper(), INTERSECTIONS, graph, MAX_SPEED)
    if not res["success"]:
        return jsonify({"status": "error", "message": res.get("error")}), 400
    return jsonify({
        "status": "success",
        "source": start.upper(),
        "destination": goal.upper(),
        "route": res["route"],
        "total_travel_time": res["total_travel_time"],
        "explored_nodes": res["explored_nodes"],
        "heuristics": res.get("heuristics", {}),
        "road_segments": res["road_segments"]
    }), 200


if __name__ == "__main__":
    # Running in debug mode for development
    app.run(debug=True, port=5000)
