"""
SmartRoute – Phase 5 End-to-End Integration Test
Simulates the exact HTTP requests and JSON payloads sent by the JavaScript frontend
to the Flask backend, ensuring the end-to-end communication contract is fulfilled.
"""

from app import app, ACTIVE_TRAFFIC

def test_full_integration():
    client = app.test_client()
    print("=" * 65)
    print("SMARTROUTE END-TO-END INTEGRATION TEST")
    print("=" * 65)

    # 1. Frontend requests network layout (GET /api/network)
    res = client.get("/api/network")
    assert res.status_code == 200
    network_data = res.get_json()["data"]
    intersections = network_data["intersections"]
    roads = network_data["roads"]
    print(f"✔ Step 1: Frontend receives road network ({len(intersections)} intersections, {len(roads)} roads).")

    # 2. User selects Source 'A' and Destination 'L' -> clicks 'Find Optimal Route'
    payload = {"source": "A", "destination": "L"}
    res = client.post("/api/find-route", json=payload)
    assert res.status_code == 200
    route_data = res.get_json()
    assert route_data["status"] == "success"
    assert route_data["route"] == ["A", "B", "E", "G", "K", "L"]
    assert route_data["total_travel_time"] == 22.0
    assert len(route_data["road_segments"]) == 5
    assert len(route_data["explored_nodes"]) >= len(route_data["route"])
    print(f"✔ Step 2: Optimal route computed without traffic: {' -> '.join(route_data['route'])} ({route_data['total_travel_time']} min).")

    # 3. User modifies traffic: Increases Road B-E to 20.0 minutes
    res = client.post("/api/update-traffic", json={"road_id": "B-E", "travel_time": 20.0})
    assert res.status_code == 200
    assert ACTIVE_TRAFFIC.get("B-E") == 20.0
    print("✔ Step 3: Traffic updated on road B-E to 20.0 min.")

    # 4. User modifies traffic: Increases Road E-G to 20.0 minutes
    res = client.post("/api/update-traffic", json={"road_id": "E-G", "travel_time": 20.0})
    assert res.status_code == 200
    print("✔ Step 4: Traffic updated on road E-G to 20.0 min.")

    # 5. Frontend re-fetches network to update SVG badges & road styles
    res = client.get("/api/network")
    assert res.status_code == 200
    updated_roads = {r["id"]: r for r in res.get_json()["data"]["roads"]}
    assert updated_roads["B-E"]["current_travel_time"] == 20.0
    assert updated_roads["B-E"]["is_modified"] is True
    print("✔ Step 5: Network data confirms modified traffic state.")

    # 6. User re-clicks 'Find Optimal Route' -> A* dynamically reroutes via Central corridor
    res = client.post("/api/find-route", json=payload)
    assert res.status_code == 200
    reroute_data = res.get_json()
    assert reroute_data["route"] == ["A", "B", "D", "J", "I", "L"]
    assert reroute_data["total_travel_time"] == 23.0
    print(f"✔ Step 6: Dynamic reroute computed: {' -> '.join(reroute_data['route'])} ({reroute_data['total_travel_time']} min).")

    # 7. User clicks 'Reset All' -> traffic resets to default
    res = client.post("/api/traffic/reset")
    assert res.status_code == 200
    assert len(ACTIVE_TRAFFIC) == 0
    print("✔ Step 7: Traffic reset successfully.")

    # 8. User recalculates route -> reverts to initial optimal route
    res = client.post("/api/find-route", json=payload)
    assert res.status_code == 200
    assert res.get_json()["route"] == ["A", "B", "E", "G", "K", "L"]
    print("✔ Step 8: Route returned to original optimal path after reset.")

    # 9. Test error response when no route exists or bad input
    res = client.post("/api/find-route", json={"source": "A", "destination": "INVALID"})
    assert res.status_code == 400
    assert "error" in res.get_json()["status"]
    print("✔ Step 9: Error handling correctly reported to frontend for invalid destination.")

    print("\n" + "=" * 65)
    print("ALL INTEGRATION TESTS PASSED PERFECTLY!")
    print("=" * 65)

if __name__ == "__main__":
    test_full_integration()
