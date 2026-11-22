"""
SmartRoute – Phase 2 Verification & Test Suite
Tests the A* Search Algorithm across multiple scenarios:
1. Admissibility and Consistency verification
2. Test Case 1: Warehouse (A) -> SIT Campus (G)
3. Test Case 2: Warehouse (A) -> Kyatsandra Hub (L)
4. Test Case 3: Town Hall (C) -> Batawadi Bypass (I)
5. Test Case 4: Dynamic Traffic Rerouting Simulation
6. Test Case 5: Invalid Input Handling & Disconnected Graph Handling
"""

import sys
from data.network import load_network_data, build_adjacency_list
from backend.astar import (
    astar_search,
    calculate_heuristic,
    verify_heuristic_consistency
)

def run_all_tests():
    data = load_network_data()
    intersections = data["intersections"]
    max_speed = data["max_speed_units_per_min"]
    base_graph = build_adjacency_list(data)

    print("=" * 65)
    print("SMARTROUTE A* SEARCH ALGORITHM TEST SUITE")
    print("=" * 65)

    # 1. Verify Consistency for all nodes
    print("\n[CHECK 1] Heuristic Consistency Verification (Monotonicity Condition):")
    all_consistent = True
    for test_goal in ["G", "H", "I", "K", "L"]:
        is_consistent, violations = verify_heuristic_consistency(
            intersections, base_graph, test_goal, max_speed
        )
        if not is_consistent:
            all_consistent = False
            print(f"  ❌ Violation found towards goal {test_goal}: {violations}")
        else:
            print(f"  ✔ Goal '{test_goal}': h(n) <= cost(n, n') + h(n') satisfied for all edges.")
    assert all_consistent, "Heuristic is not consistent!"
    print("  --> Heuristic is strictly ADMISSIBLE and CONSISTENT.\n")

    # 2. Test Case 1: A -> G
    print("-" * 65)
    print("TEST CASE 1: Warehouse (A) -> SIT Campus Cross (G)")
    res1 = astar_search("A", "G", intersections, base_graph, max_speed)
    print(f"  Status: {'SUCCESS' if res1['success'] else 'FAILED'}")
    print(f"  Optimal Route: {' -> '.join(res1['route'])}")
    print(f"  Total Travel Time: {res1['total_travel_time']} mins")
    print(f"  Explored Nodes: {res1['explored_nodes']}")
    assert res1["success"]
    assert res1["route"] == ["A", "B", "E", "G"]
    assert res1["total_travel_time"] == 13.0

    # 3. Test Case 2: A -> L (Eastmost delivery hub)
    print("-" * 65)
    print("TEST CASE 2: Warehouse (A) -> Kyatsandra Hub (L)")
    res2 = astar_search("A", "L", intersections, base_graph, max_speed)
    print(f"  Status: {'SUCCESS' if res2['success'] else 'FAILED'}")
    print(f"  Optimal Route: {' -> '.join(res2['route'])}")
    print(f"  Total Travel Time: {res2['total_travel_time']} mins")
    print(f"  Explored Nodes: {res2['explored_nodes']}")
    assert res2["success"]
    # Path via B-E-G-K-L = 5.0 + 4.0 + 4.0 + 4.5 + 4.5 = 22.0 mins
    assert res2["total_travel_time"] == 22.0

    # 4. Test Case 3: C -> I
    print("-" * 65)
    print("TEST CASE 3: Town Hall Square (C) -> Batawadi Bypass (I)")
    res3 = astar_search("C", "I", intersections, base_graph, max_speed)
    print(f"  Status: {'SUCCESS' if res3['success'] else 'FAILED'}")
    print(f"  Optimal Route: {' -> '.join(res3['route'])}")
    print(f"  Total Travel Time: {res3['total_travel_time']} mins")
    print(f"  Explored Nodes: {res3['explored_nodes']}")
    assert res3["success"]
    # Path C -> D -> J -> I: 5.5 + 5.0 + 4.0 = 14.5 mins
    assert res3["route"] == ["C", "D", "J", "I"]
    assert res3["total_travel_time"] == 14.5

    # 5. Test Case 4: Traffic Simulation on A -> L
    print("-" * 65)
    print("TEST CASE 4: Dynamic Traffic Rerouting Simulation")
    print("  Applying heavy traffic jam to North bypass roads: B-E (+15 min) and E-G (+15 min)")
    traffic_graph = build_adjacency_list(data, {"B-E": 19.0, "E-G": 19.0})
    res_traffic = astar_search("A", "L", intersections, traffic_graph, max_speed)
    print(f"  New Route without Jam: {' -> '.join(res_traffic['route'])}")
    print(f"  New Total Travel Time: {res_traffic['total_travel_time']} mins")
    print(f"  Explored Nodes: {res_traffic['explored_nodes']}")
    # Should dynamically reroute via Central spine A -> B -> D -> J -> I -> L (23.0 mins)
    assert res_traffic["route"] == ["A", "B", "D", "J", "I", "L"]
    assert res_traffic["total_travel_time"] == 23.0
    print("  ✔ Successfully rerouted around traffic bottleneck!")

    # 6. Test Case 5: Error Handling
    print("-" * 65)
    print("TEST CASE 5: Error and Edge Case Handling")
    # Invalid start
    err1 = astar_search("Z", "L", intersections, base_graph, max_speed)
    print(f"  Invalid Start ('Z'): {err1['error']}")
    assert not err1["success"]

    # Invalid goal
    err2 = astar_search("A", "99", intersections, base_graph, max_speed)
    print(f"  Invalid Goal ('99'): {err2['error']}")
    assert not err2["success"]

    # Start == Goal
    same = astar_search("A", "A", intersections, base_graph, max_speed)
    print(f"  Start equals Goal ('A' -> 'A'): {same['route']} in {same['total_travel_time']} mins")
    assert same["success"] and same["total_travel_time"] == 0.0

    # Disconnected graph (isolated island node)
    disconnected_graph = {node: [] for node in intersections}
    err3 = astar_search("A", "L", intersections, disconnected_graph, max_speed)
    print(f"  Disconnected graph: {err3['error']}")
    assert not err3["success"]

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
