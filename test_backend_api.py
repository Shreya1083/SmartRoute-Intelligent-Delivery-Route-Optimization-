"""
SmartRoute – Phase 3 Backend API Test Suite
Validates all Flask endpoints, CORS headers, inputs, error states, and traffic simulation.
"""

from app import app, ACTIVE_TRAFFIC

def run_api_tests():
    client = app.test_client()

    print("=" * 65)
    print("SMARTROUTE BACKEND API TEST SUITE")
    print("=" * 65)

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    print("✔ [1/8] GET /api/health -> 200 OK:", res.get_json()["message"])

    # 2. CORS header check
    assert res.headers.get("Access-Control-Allow-Origin") == "*"
    print("✔ [2/8] CORS headers verified: Access-Control-Allow-Origin = '*'")

    # 3. GET /api/network
    res = client.get("/api/network")
    assert res.status_code == 200
    net = res.get_json()["data"]
    assert len(net["intersections"]) == 12
    assert len(net["roads"]) == 18
    print(f"✔ [3/8] GET /api/network -> 200 OK: {len(net['intersections'])} nodes, {len(net['roads'])} roads")

    # 4. POST /api/find-route (Normal Route A -> L)
    res = client.post("/api/find-route", json={"source": "A", "destination": "L"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["route"] == ["A", "B", "E", "G", "K", "L"]
    assert data["total_travel_time"] == 22.0
    assert "heuristics" in data
    assert "explored_nodes" in data
    print(f"✔ [4/8] POST /api/find-route (A -> L) -> 200 OK: Route {' -> '.join(data['route'])}, Time: {data['total_travel_time']} min")

    # 5. POST /api/update-traffic
    res = client.post("/api/update-traffic", json={"road_id": "B-E", "travel_time": 25.0})
    assert res.status_code == 200
    traffic_res = res.get_json()
    assert traffic_res["road"]["current_travel_time"] == 25.0
    print("✔ [5/8] POST /api/update-traffic -> 200 OK: Road B-E increased to 25.0 mins")

    # 6. Verify dynamic rerouting on POST /api/find-route after traffic update
    res = client.post("/api/find-route", json={"source": "A", "destination": "L"})
    assert res.status_code == 200
    reroute_data = res.get_json()
    # Path should now avoid B-E and take central spine A -> B -> D -> J -> I -> L (23.0 min)
    assert reroute_data["route"] == ["A", "B", "D", "J", "I", "L"]
    assert reroute_data["total_travel_time"] == 23.0
    print(f"✔ [6/8] POST /api/find-route with traffic -> Dynamic Reroute: {' -> '.join(reroute_data['route'])}, Time: {reroute_data['total_travel_time']} min")

    # 7. POST /api/traffic/reset
    res = client.post("/api/traffic/reset")
    assert res.status_code == 200
    assert len(ACTIVE_TRAFFIC) == 0
    # Re-run route to confirm it reverts to optimal
    res = client.post("/api/find-route", json={"source": "A", "destination": "L"})
    assert res.get_json()["route"] == ["A", "B", "E", "G", "K", "L"]
    print("✔ [7/8] POST /api/traffic/reset -> 200 OK: Reset verified, original path restored")

    # 8. Validation and Error Handling Tests
    print("✔ [8/8] Validating Error Handling Cases:")

    # Missing JSON body
    res = client.post("/api/find-route", data="non-json string")
    assert res.status_code == 400
    print("   - Non-JSON request rejected with 400:", res.get_json()["message"])

    # Missing destination
    res = client.post("/api/find-route", json={"source": "A"})
    assert res.status_code == 400
    print("   - Missing destination rejected with 400:", res.get_json()["message"])

    # Invalid source node
    res = client.post("/api/find-route", json={"source": "UNKNOWN", "destination": "L"})
    assert res.status_code == 400
    print("   - Invalid source node rejected with 400:", res.get_json()["message"])

    # Invalid road_id in traffic update
    res = client.post("/api/update-traffic", json={"road_id": "ROAD-XYZ", "travel_time": 10.0})
    assert res.status_code == 400
    print("   - Invalid road_id rejected with 400:", res.get_json()["message"])

    # Negative travel time in traffic update
    res = client.post("/api/update-traffic", json={"road_id": "A-B", "travel_time": -5.0})
    assert res.status_code == 400
    print("   - Negative travel time rejected with 400:", res.get_json()["message"])

    print("\n" + "=" * 65)
    print("ALL 8 BACKEND API SUITE TESTS PASSED!")
    print("=" * 65)

if __name__ == "__main__":
    run_api_tests()
