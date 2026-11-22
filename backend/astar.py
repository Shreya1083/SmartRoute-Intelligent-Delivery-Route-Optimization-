"""
SmartRoute – A* Search Algorithm Implementation
Finds the minimum travel-time path between a warehouse and delivery destinations.

Evaluation Function:
    f(n) = g(n) + h(n)
Where:
    g(n) = Actual travel time from start intersection to intersection n.
    h(n) = Estimated remaining travel time from n to goal intersection.
    f(n) = Total estimated travel time for a path through n.
"""

import heapq
import math


def calculate_heuristic(node_a, node_b, intersections, max_speed=40.0):
    """
    Step 1: Heuristic Calculation
    Calculates the Euclidean (straight-line) distance between two intersections
    and converts it into an estimated minimum travel time using the maximum vehicle speed:
    
        h(n) = EuclideanDistance(node_a, node_b) / max_speed
    
    Admissibility & Consistency:
    - Euclidean distance is the shortest possible physical distance between two points.
    - max_speed is the upper bound on vehicle speed across the road network.
    - Therefore, h(n) <= true remaining travel time (never overestimates).
    - By the triangle inequality, h(n) <= cost(n, n') + h(n') (monotonically consistent).
    """
    if node_a not in intersections or node_b not in intersections:
        return 0.0

    pos_a = intersections[node_a]
    pos_b = intersections[node_b]

    # Euclidean distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
    euclidean_dist = math.hypot(pos_b["x"] - pos_a["x"], pos_b["y"] - pos_a["y"])

    # Estimated travel time in minutes
    return euclidean_dist / max_speed


def verify_heuristic_consistency(intersections, adjacency_list, goal_node, max_speed=40.0):
    """
    Verifies that the heuristic satisfies the consistency (monotonicity) condition:
        h(n) <= cost(n, n') + h(n')
    for all edges (n, n') in the graph towards the given goal_node.
    Returns:
        (is_consistent: bool, violations: list)
    """
    violations = []
    
    for n, edges in adjacency_list.items():
        h_n = calculate_heuristic(n, goal_node, intersections, max_speed)
        for edge in edges:
            n_prime = edge["neighbor"]
            cost = edge["cost"]
            h_n_prime = calculate_heuristic(n_prime, goal_node, intersections, max_speed)
            
            # Consistency check with tiny floating-point tolerance (1e-7)
            if h_n > cost + h_n_prime + 1e-7:
                violations.append({
                    "from": n,
                    "to": n_prime,
                    "h(n)": round(h_n, 4),
                    "cost": round(cost, 4),
                    "h(n')": round(h_n_prime, 4),
                    "difference": round(h_n - (cost + h_n_prime), 4)
                })

    return len(violations) == 0, violations


def astar_search(start_node, goal_node, intersections, adjacency_list, max_speed=40.0):
    """
    Step 2: A* Search Algorithm Implementation using a Priority Queue.
    
    Inputs:
        start_node: Starting intersection ID (e.g. 'A')
        goal_node: Target intersection ID (e.g. 'L')
        intersections: Dictionary containing node metadata and coordinates
        adjacency_list: Dictionary mapping node -> list of outgoing edges
        max_speed: Maximum possible vehicle speed (for heuristic calculation)

    Returns:
        dict containing:
            success (bool): Whether a path was found
            route (list): Ordered list of intersection IDs from start to goal
            total_travel_time (float): Sum of road travel times in minutes
            explored_nodes (list): Nodes visited in order of evaluation
            road_segments (list): Edges traversed along the optimal route
            error (str, optional): Error message if path not found or input invalid
    """
    # 1. Input Validation: Check if intersections exist in the network
    if start_node not in intersections:
        return {
            "success": False,
            "error": f"Invalid start intersection '{start_node}'. Please choose a valid node."
        }
    if goal_node not in intersections:
        return {
            "success": False,
            "error": f"Invalid destination intersection '{goal_node}'. Please choose a valid node."
        }

    # 2. Trivial Case: Start is already the goal
    if start_node == goal_node:
        return {
            "success": True,
            "route": [start_node],
            "total_travel_time": 0.0,
            "explored_nodes": [start_node],
            "road_segments": [],
            "heuristics": {start_node: 0.0}
        }

    # 3. Data Structures for A* Search
    # Priority Queue (open set): entries are (f_score, tie_breaker_id, current_node)
    open_heap = []
    tie_breaker = 0

    # g_score: actual travel time from start to each node (initially infinity)
    g_score = {node: float("inf") for node in intersections}
    g_score[start_node] = 0.0

    # Initial f_score for start_node: f(start) = g(start) + h(start, goal) = 0 + h(start, goal)
    f_start = calculate_heuristic(start_node, goal_node, intersections, max_speed)
    heapq.heappush(open_heap, (f_start, tie_breaker, start_node))

    # parent mapping to reconstruct the shortest path: parent[node] = (predecessor, road_id, cost)
    parent = {}

    # closed set: tracks permanently expanded nodes
    closed_set = set()

    # explored_nodes: ordered history of nodes popped from priority queue
    explored_nodes = []

    goal_reached = False

    # 4. Search Loop
    while open_heap:
        # Pop the node with the lowest f(n) = g(n) + h(n)
        current_f, _, current = heapq.heappop(open_heap)

        # Skip if this node has already been permanently evaluated
        if current in closed_set:
            continue

        closed_set.add(current)
        explored_nodes.append(current)

        # 5. Goal Test
        if current == goal_node:
            goal_reached = True
            break

        # 6. Examine all neighbors of current intersection
        for edge in adjacency_list.get(current, []):
            neighbor = edge["neighbor"]
            travel_time = edge["cost"]
            road_id = edge["road_id"]

            # Ignore already evaluated nodes
            if neighbor in closed_set:
                continue

            # Tentative g score: cost from start to current + cost of edge (current -> neighbor)
            tentative_g = g_score[current] + travel_time

            # If this path to neighbor is strictly faster than any previous path
            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                parent[neighbor] = (current, road_id, travel_time)
                
                # Compute heuristic h(neighbor) and total estimated f(neighbor) = g + h
                h_neighbor = calculate_heuristic(neighbor, goal_node, intersections, max_speed)
                f_neighbor = tentative_g + h_neighbor
                
                tie_breaker += 1
                heapq.heappush(open_heap, (f_neighbor, tie_breaker, neighbor))

    # 7. Check if a route was found
    if not goal_reached:
        return {
            "success": False,
            "error": f"No route exists between '{start_node}' and '{goal_node}'.",
            "explored_nodes": explored_nodes
        }

    # 8. Path Reconstruction: Backtrack from goal to start using parent pointers
    route = []
    road_segments = []
    curr = goal_node

    while curr in parent:
        prev, road_id, cost = parent[curr]
        route.append(curr)
        road_segments.append({
            "road_id": road_id,
            "from": prev,
            "to": curr,
            "travel_time": cost
        })
        curr = prev

    route.append(start_node)
    
    # Reverse to get order from start to goal
    route.reverse()
    road_segments.reverse()

    # Calculate heuristic values h(n) for all nodes relative to goal
    heuristics = {
        node: round(calculate_heuristic(node, goal_node, intersections, max_speed), 2)
        for node in intersections
    }

    return {
        "success": True,
        "route": route,
        "total_travel_time": round(g_score[goal_node], 2),
        "explored_nodes": explored_nodes,
        "road_segments": road_segments,
        "heuristics": heuristics
    }
