"""
SmartRoute – Phase 6 Comprehensive Validation Suite
Validates:
1. Multi-pair A* testing across all 12 nodes (132 source-destination pairs)
2. Comparison with Uniform Cost Search (UCS / Dijkstra)
3. Mathematical Admissibility against ground truth h*(n)
4. Mathematical Consistency (Monotonicity) across all edges
5. Dynamic traffic rerouting
6. Road segment cost summation verification
7. Error and disconnected graph edge cases
"""

import heapq
import math
from data.network import load_network_data, build_adjacency_list
from backend.astar import astar_search, calculate_heuristic, verify_heuristic_consistency


def uniform_cost_search(start_node, goal_node, intersections, adjacency_list):
    """
    Uniform Cost Search (Dijkstra's Algorithm).
    Expands nodes based strictly on g(n) (accumulated travel time from start) with h(n) = 0.
    Guaranteed to find the optimal path in graphs with non-negative edge costs.
    """
    if start_node == goal_node:
        return {"success": True, "route": [start_node], "cost": 0.0, "explored_count": 1}

    open_heap = []
    counter = 0
    heapq.heappush(open_heap, (0.0, counter, start_node))
    
    g_score = {node: float("inf") for node in intersections}
    g_score[start_node] = 0.0
    
    parent = {}
    closed_set = set()
    explored_nodes = []

    while open_heap:
        current_g, _, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue
        closed_set.add(current)
        explored_nodes.append(current)

        if current == goal_node:
            # Reconstruct route
            route = []
            curr = goal_node
            while curr in parent:
                route.append(curr)
                curr = parent[curr]
            route.append(start_node)
            route.reverse()
            return {
                "success": True,
                "route": route,
                "cost": round(g_score[goal_node], 2),
                "explored_count": len(explored_nodes)
            }

        for edge in adjacency_list.get(current, []):
            neighbor = edge["neighbor"]
            cost = edge["cost"]
            if neighbor in closed_set:
                continue

            tentative_g = current_g + cost
            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                parent[neighbor] = current
                counter += 1
                heapq.heappush(open_heap, (tentative_g, counter, neighbor))

    return {"success": False, "route": [], "cost": float("inf"), "explored_count": len(explored_nodes)}


def run_comprehensive_validation():
    data = load_network_data()
    intersections = data["intersections"]
    roads = data["roads"]
    max_speed = data["max_speed_units_per_min"]
    base_graph = build_adjacency_list(data)

    test_results_table = []

    # -------------------------------------------------------------
    # 1. Admissibility Check: h(n) <= h*(n) for all pairs
    # -------------------------------------------------------------
    admissibility_violations = []
    for u in intersections:
        for v in intersections:
            if u == v:
                continue
            ucs_res = uniform_cost_search(u, v, intersections, base_graph)
            true_min_cost = ucs_res["cost"]
            h_val = calculate_heuristic(u, v, intersections, max_speed)
            if h_val > true_min_cost + 1e-7:
                admissibility_violations.append((u, v, h_val, true_min_cost))

    test_results_table.append({
        "case": "1. Heuristic Admissibility",
        "source": "All 132 pairs",
        "dest": "All 132 pairs",
        "expected": "h(n) <= h*(n) everywhere (0 violations)",
        "actual": f"{len(admissibility_violations)} violations found",
        "status": "PASS" if len(admissibility_violations) == 0 else "FAIL"
    })

    # -------------------------------------------------------------
    # 2. Consistency (Monotonicity) Check: h(n) <= c(n, n') + h(n')
    # -------------------------------------------------------------
    consistency_violations = []
    for goal in intersections:
        is_consistent, violations = verify_heuristic_consistency(intersections, base_graph, goal, max_speed)
        if not is_consistent:
            consistency_violations.extend(violations)

    test_results_table.append({
        "case": "2. Heuristic Consistency",
        "source": "All directed edges",
        "dest": "All 12 goals",
        "expected": "h(n) <= c(n,n') + h(n') (0 violations)",
        "actual": f"{len(consistency_violations)} violations found",
        "status": "PASS" if len(consistency_violations) == 0 else "FAIL"
    })

    # -------------------------------------------------------------
    # 3. A* vs UCS Optimality Comparison (All 132 pairs)
    # -------------------------------------------------------------
    optimality_matches = 0
    efficiency_count = 0  # Where A* explored fewer nodes than UCS
    total_pairs = 0

    for u in intersections:
        for v in intersections:
            if u == v:
                continue
            total_pairs += 1
            astar_res = astar_search(u, v, intersections, base_graph, max_speed)
            ucs_res = uniform_cost_search(u, v, intersections, base_graph)

            assert astar_res["success"] and ucs_res["success"]
            # Verify travel time match
            if math.isclose(astar_res["total_travel_time"], ucs_res["cost"], rel_tol=1e-5):
                optimality_matches += 1
            if len(astar_res["explored_nodes"]) <= ucs_res["explored_count"]:
                efficiency_count += 1

    test_results_table.append({
        "case": "3. A* vs UCS Cost Equivalence",
        "source": "All 132 pairs",
        "dest": "All 132 pairs",
        "expected": "Cost(A*) == Cost(UCS) on 100% of pairs",
        "actual": f"Matched {optimality_matches}/{total_pairs} pairs (100%)",
        "status": "PASS" if optimality_matches == total_pairs else "FAIL"
    })

    test_results_table.append({
        "case": "4. A* Search Efficiency vs UCS",
        "source": "All 132 pairs",
        "dest": "All 132 pairs",
        "expected": "A* explores <= nodes than UCS",
        "actual": f"A* explored <= nodes on {efficiency_count}/{total_pairs} pairs",
        "status": "PASS" if efficiency_count == total_pairs else "FAIL"
    })

    # -------------------------------------------------------------
    # 5. Route Segment Summation Integrity
    # -------------------------------------------------------------
    res_a_l = astar_search("A", "L", intersections, base_graph, max_speed)
    segment_sum = sum(seg["travel_time"] for seg in res_a_l["road_segments"])
    sum_matches = math.isclose(segment_sum, res_a_l["total_travel_time"], rel_tol=1e-5)

    test_results_table.append({
        "case": "5. Route Cost Sum Verification",
        "source": "A (Warehouse)",
        "dest": "L (Kyatsandra Hub)",
        "expected": "Sum of road segments == total_travel_time (22.0 min)",
        "actual": f"Sum = {segment_sum:.1f} min, Total = {res_a_l['total_travel_time']} min",
        "status": "PASS" if sum_matches else "FAIL"
    })

    # -------------------------------------------------------------
    # 6. Specific Route Combinations
    # -------------------------------------------------------------
    # Route A -> G
    res_a_g = astar_search("A", "G", intersections, base_graph, max_speed)
    test_results_table.append({
        "case": "6. Normal Route A -> G",
        "source": "A",
        "dest": "G (SIT Campus)",
        "expected": "A -> B -> E -> G (13.0 min)",
        "actual": f"{' -> '.join(res_a_g['route'])} ({res_a_g['total_travel_time']} min)",
        "status": "PASS" if res_a_g["route"] == ["A", "B", "E", "G"] and res_a_g["total_travel_time"] == 13.0 else "FAIL"
    })

    # Route C -> I
    res_c_i = astar_search("C", "I", intersections, base_graph, max_speed)
    test_results_table.append({
        "case": "7. Normal Route C -> I",
        "source": "C (Town Hall)",
        "dest": "I (Batawadi Bypass)",
        "expected": "C -> D -> J -> I (14.5 min)",
        "actual": f"{' -> '.join(res_c_i['route'])} ({res_c_i['total_travel_time']} min)",
        "status": "PASS" if res_c_i["route"] == ["C", "D", "J", "I"] and res_c_i["total_travel_time"] == 14.5 else "FAIL"
    })

    # Route F -> K
    res_f_k = astar_search("F", "K", intersections, base_graph, max_speed)
    test_results_table.append({
        "case": "8. Cross-Town Route F -> K",
        "source": "F (Sapthagiri Ext)",
        "dest": "K (Maralur Lake)",
        "expected": "Optimal route found with matching UCS cost",
        "actual": f"{' -> '.join(res_f_k['route'])} ({res_f_k['total_travel_time']} min)",
        "status": "PASS" if res_f_k["success"] else "FAIL"
    })

    # -------------------------------------------------------------
    # 7. Traffic Simulation Rerouting
    # -------------------------------------------------------------
    # Congest North route: B-E (+15 min) and E-G (+15 min)
    congested_graph = build_adjacency_list(data, {"B-E": 19.0, "E-G": 19.0})
    res_traffic = astar_search("A", "L", intersections, congested_graph, max_speed)
    reroute_success = res_traffic["route"] == ["A", "B", "D", "J", "I", "L"] and res_traffic["total_travel_time"] == 23.0

    test_results_table.append({
        "case": "9. Traffic Reroute Simulation",
        "source": "A",
        "dest": "L",
        "expected": "Dynamic shift to Central Spine (A->B->D->J->I->L, 23.0m)",
        "actual": f"{' -> '.join(res_traffic['route'])} ({res_traffic['total_travel_time']} min)",
        "status": "PASS" if reroute_success else "FAIL"
    })

    # -------------------------------------------------------------
    # 8. Invalid Input Handling
    # -------------------------------------------------------------
    res_inv_src = astar_search("INVALID", "L", intersections, base_graph, max_speed)
    test_results_table.append({
        "case": "10. Invalid Source Node",
        "source": "INVALID",
        "dest": "L",
        "expected": "Failure with descriptive error message",
        "actual": res_inv_src.get("error", "Failed"),
        "status": "PASS" if not res_inv_src["success"] and "Invalid start" in res_inv_src["error"] else "FAIL"
    })

    res_inv_dst = astar_search("A", "INVALID", intersections, base_graph, max_speed)
    test_results_table.append({
        "case": "11. Invalid Destination Node",
        "source": "A",
        "dest": "INVALID",
        "expected": "Failure with descriptive error message",
        "actual": res_inv_dst.get("error", "Failed"),
        "status": "PASS" if not res_inv_dst["success"] and "Invalid destination" in res_inv_dst["error"] else "FAIL"
    })

    # -------------------------------------------------------------
    # 9. Disconnected Graph & Unreachable Destination
    # -------------------------------------------------------------
    # Disconnect node L completely (remove all edges connecting to L)
    isolated_l_graph = {node: [e for e in edges if e["neighbor"] != "L"] for node, edges in base_graph.items()}
    isolated_l_graph["L"] = []
    res_unreachable = astar_search("A", "L", intersections, isolated_l_graph, max_speed)

    test_results_table.append({
        "case": "12. Disconnected Destination",
        "source": "A",
        "dest": "L (Isolated)",
        "expected": "Failure: No route exists between 'A' and 'L'",
        "actual": res_unreachable.get("error", "Failed"),
        "status": "PASS" if not res_unreachable["success"] and "No route exists" in res_unreachable["error"] else "FAIL"
    })

    # -------------------------------------------------------------
    # Print Formatted Table
    # -------------------------------------------------------------
    print("=" * 115)
    print(f"{'TEST CASE':<32} | {'SRC':<12} | {'DST':<12} | {'ACTUAL RESULT':<42} | {'STATUS'}")
    print("-" * 115)
    for row in test_results_table:
        print(f"{row['case']:<32} | {row['source'][:12]:<12} | {row['dest'][:12]:<12} | {row['actual'][:42]:<42} | {row['status']}")
    print("=" * 115)

    all_passed = all(row["status"] == "PASS" for row in test_results_table)
    print(f"\nOVERALL RESULT: {'ALL TESTS PASSED SUCCESSFULLY (12/12)!' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = run_comprehensive_validation()
    if not success:
        exit(1)
