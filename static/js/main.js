/**
 * SmartRoute – Intelligent Delivery Route Optimization
 * Client-Side JavaScript Application
 *
 * Responsibilities:
 * 1. Fetch network dataset and active traffic state from Flask API.
 * 2. Dynamically render the SVG road network (nodes, roads, cost badges).
 * 3. Populate source, destination, and road selection dropdowns.
 * 4. Submit route planning requests to A* backend (/api/find-route).
 * 5. Visually highlight the optimal path and explored nodes on the SVG map.
 * 6. Handle traffic simulation modifications and live rerouting.
 */

// Application State
const state = {
    network: null,            // Raw network data (intersections, roads, etc.)
    activeRoute: null,        // Last computed route result
    activeTraffic: {},        // Current road overrides: { roadId: cost }
    apiBaseUrl: ''            // Local Flask API (same-origin)
};

// DOM Element References
const dom = {
    sourceSelect: document.getElementById('source-select'),
    destinationSelect: document.getElementById('destination-select'),
    routeForm: document.getElementById('route-form'),
    btnFindRoute: document.getElementById('btn-find-route'),

    // Results Card Elements
    resultsPlaceholder: document.getElementById('results-placeholder'),
    resultsContent: document.getElementById('results-content'),
    metricTravelTime: document.getElementById('metric-travel-time'),
    metricExploredCount: document.getElementById('metric-explored-count'),
    metricRouteSteps: document.getElementById('metric-route-steps'),
    optimalPathBadges: document.getElementById('optimal-path-badges'),
    exploredNodesList: document.getElementById('explored-nodes-list'),
    legsTableBody: document.getElementById('legs-table-body'),

    // Traffic Simulation Elements
    trafficRoadSelect: document.getElementById('traffic-road-select'),
    trafficTimeInput: document.getElementById('traffic-time-input'),
    btnUpdateTraffic: document.getElementById('btn-update-traffic'),
    btnResetTraffic: document.getElementById('btn-reset-traffic'),
    activeTrafficContainer: document.getElementById('active-traffic-container'),
    activeTrafficList: document.getElementById('active-traffic-list'),

    // SVG Layers
    svg: document.getElementById('road-network-svg'),
    edgesLayer: document.getElementById('svg-edges-layer'),
    routeLayer: document.getElementById('svg-route-layer'),
    edgeLabelsLayer: document.getElementById('svg-edge-labels-layer'),
    nodesLayer: document.getElementById('svg-nodes-layer'),
    btnResetMap: document.getElementById('btn-reset-map'),

    // Notification Banner
    statusBanner: document.getElementById('status-banner'),
    statusMessage: document.getElementById('status-message'),
    bannerClose: document.getElementById('banner-close')
};

// ============================================================
// 1. INITIALIZATION & LIFECYCLE
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadNetworkData();
});

function initEventListeners() {
    // Route optimization submission
    dom.routeForm.addEventListener('submit', onFindRouteSubmit);

    // Traffic road selector change -> update input with current road time
    dom.trafficRoadSelect.addEventListener('change', onTrafficRoadChange);

    // Traffic update button
    dom.btnUpdateTraffic.addEventListener('click', onUpdateTrafficClick);

    // Traffic reset button
    dom.btnResetTraffic.addEventListener('click', onResetTrafficClick);

    // Traffic quick preset buttons (+5, +10, +15 min)
    document.querySelectorAll('.btn-preset[data-add]').forEach(btn => {
        btn.addEventListener('click', () => {
            const addTime = parseFloat(btn.dataset.add);
            const currentVal = parseFloat(dom.trafficTimeInput.value) || 5;
            dom.trafficTimeInput.value = (currentVal + addTime).toFixed(1);
        });
    });

    // Reset map highlights button
    dom.btnResetMap.addEventListener('click', () => {
        clearHighlights();
        state.activeRoute = null;
        dom.resultsContent.classList.add('hidden');
        dom.resultsPlaceholder.classList.remove('hidden');
        dom.resultsPlaceholder.innerHTML = '<p>Select a source and destination, then click <strong>Find Optimal Route</strong> to view A* path metrics.</p>';
        showBanner('Map highlights cleared.', 'info');
    });

    // Banner close button
    dom.bannerClose.addEventListener('click', () => {
        dom.statusBanner.classList.add('hidden');
    });
}

// ============================================================
// 2. DATA FETCHING (FLASK REST API)
// ============================================================
async function loadNetworkData() {
    try {
        showBanner('Loading Tumakuru road network...', 'info');
        const response = await fetch(`${state.apiBaseUrl}/api/network`);
        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }
        const json = await response.json();
        state.network = json.data;
        state.activeTraffic = json.data.active_traffic_overrides || {};

        populateDropdowns();
        renderSvgNetwork();
        updateActiveTrafficList();
        showBanner('Road network loaded. Select source and destination to plan a route.', 'success');
    } catch (err) {
        console.error('Failed to load network:', err);
        showBanner(`Unable to connect to Flask backend: ${err.message}. Make sure "python app.py" is running.`, 'error');
    }
}

// ============================================================
// 3. UI DROPDOWNS POPULATION
// ============================================================
function populateDropdowns() {
    if (!state.network) return;

    const { intersections, warehouse, destinations, roads } = state.network;

    // 1. Source Dropdown (default warehouse 'A')
    dom.sourceSelect.innerHTML = '';
    Object.keys(intersections).sort().forEach(id => {
        const item = intersections[id];
        const isWarehouse = id === warehouse;
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = `${id} – ${item.name} ${isWarehouse ? '(Warehouse)' : ''}`;
        if (isWarehouse) opt.selected = true;
        dom.sourceSelect.appendChild(opt);
    });

    // 2. Destination Dropdown (default first destination, e.g. 'L' or 'G')
    dom.destinationSelect.innerHTML = '';
    Object.keys(intersections).sort().forEach(id => {
        const item = intersections[id];
        const isDest = destinations.includes(id);
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = `${id} – ${item.name} ${isDest ? '★ (Delivery Destination)' : ''}`;
        if (id === 'L' || (isDest && !dom.destinationSelect.value)) {
            opt.selected = true;
        }
        dom.destinationSelect.appendChild(opt);
    });

    // 3. Traffic Road Select
    dom.trafficRoadSelect.innerHTML = '';
    roads.forEach(road => {
        const opt = document.createElement('option');
        opt.value = road.id;
        opt.textContent = `${road.id} (${road.from} ↔ ${road.to}): ${road.name} [${road.current_travel_time}m]`;
        dom.trafficRoadSelect.appendChild(opt);
    });

    if (roads.length > 0) {
        dom.trafficRoadSelect.value = roads[0].id;
        dom.trafficTimeInput.value = roads[0].current_travel_time;
    }
}

function onTrafficRoadChange() {
    const selectedId = dom.trafficRoadSelect.value;
    const road = state.network.roads.find(r => r.id === selectedId);
    if (road) {
        dom.trafficTimeInput.value = road.current_travel_time;
    }
}

// ============================================================
// 4. SVG ROAD NETWORK RENDERING
// ============================================================
function renderSvgNetwork() {
    if (!state.network) return;

    const { intersections, roads, warehouse, destinations } = state.network;

    // Clear existing SVG layers
    dom.edgesLayer.innerHTML = '';
    dom.routeLayer.innerHTML = '';
    dom.edgeLabelsLayer.innerHTML = '';
    dom.nodesLayer.innerHTML = '';

    // A. Render Road Edges (Lines)
    roads.forEach(road => {
        const u = intersections[road.from];
        const v = intersections[road.to];
        if (!u || !v) return;

        const isCongested = road.is_modified && road.current_travel_time > road.base_travel_time;

        // Base Road Line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', u.x);
        line.setAttribute('y1', u.y);
        line.setAttribute('x2', v.x);
        line.setAttribute('y2', v.y);
        line.setAttribute('id', `edge-${road.id}`);
        line.setAttribute('class', `svg-road-edge ${isCongested ? 'congested' : ''}`);

        // Tooltip title
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `${road.id}: ${road.name} | Travel Time: ${road.current_travel_time} min`;
        line.appendChild(title);

        // Click road to populate traffic form
        line.addEventListener('click', () => {
            dom.trafficRoadSelect.value = road.id;
            dom.trafficTimeInput.value = road.current_travel_time;
            showBanner(`Selected road ${road.id} (${road.name}) for traffic simulation.`, 'info');
        });

        dom.edgesLayer.appendChild(line);

        // B. Travel-Time Cost Badge along the road
        renderEdgeCostBadge(road, u, v, isCongested);
    });

    // C. Render Intersections (Nodes)
    Object.keys(intersections).forEach(id => {
        const node = intersections[id];
        const isWarehouse = id === warehouse;
        const isDestination = destinations.includes(id);

        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('id', `node-group-${id}`);
        group.setAttribute('class', `svg-node-group ${isWarehouse ? 'is-warehouse' : ''} ${isDestination ? 'is-destination' : ''}`);
        group.setAttribute('transform', `translate(${node.x}, ${node.y})`);

        // Circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', isWarehouse ? '18' : '15');
        circle.setAttribute('class', 'svg-node-circle');
        group.appendChild(circle);

        // Node ID Text (A, B, C...)
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'svg-node-text');
        text.textContent = id;
        group.appendChild(text);

        // Node Name Label underneath
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('y', '26');
        label.setAttribute('class', 'svg-node-label');
        // Shorten long labels for SVG cleanliness
        label.textContent = node.name.split('(')[0].trim();
        group.appendChild(label);

        // Tooltip
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `${id}: ${node.name} (${node.type}) [x:${node.x}, y:${node.y}]`;
        group.appendChild(title);

        // Click node to select as source (if left click) or destination
        group.addEventListener('click', () => {
            if (id === warehouse || dom.sourceSelect.value === id) {
                dom.sourceSelect.value = id;
            } else {
                dom.destinationSelect.value = id;
            }
            showBanner(`Selected intersection ${id} (${node.name}).`, 'info');
        });

        dom.nodesLayer.appendChild(group);
    });
}

function renderEdgeCostBadge(road, u, v, isCongested) {
    // Calculate midpoint of the road edge
    const midX = (u.x + v.x) / 2;
    const midY = (u.y + v.y) / 2;

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', `edge-cost-badge ${isCongested ? 'congested-badge' : ''}`);
    g.setAttribute('transform', `translate(${midX}, ${midY})`);

    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', '-18');
    rect.setAttribute('y', '-10');
    rect.setAttribute('width', '36');
    rect.setAttribute('height', '20');

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.textContent = `${road.current_travel_time}m`;

    g.appendChild(rect);
    g.appendChild(text);

    // Click badge to select road for traffic editing
    g.addEventListener('click', (e) => {
        e.stopPropagation();
        dom.trafficRoadSelect.value = road.id;
        dom.trafficTimeInput.value = road.current_travel_time;
        showBanner(`Selected road ${road.id} for traffic simulation.`, 'info');
    });

    dom.edgeLabelsLayer.appendChild(g);
}

// ============================================================
// 5. ROUTE OPTIMIZATION (POST /api/find-route)
// ============================================================
async function onFindRouteSubmit(e) {
    e.preventDefault();

    const source = dom.sourceSelect.value;
    const destination = dom.destinationSelect.value;

    if (!source || !destination) {
        showBanner('Please select both a source and destination intersection.', 'error');
        return;
    }

    try {
        setLoadingState(true);
        showBanner(`Executing A* Search from ${source} to ${destination}...`, 'info');

        const response = await fetch(`${state.apiBaseUrl}/api/find-route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, destination })
        });

        const data = await response.json();

        if (!response.ok || data.status !== 'success') {
            throw new Error(data.message || 'Route calculation failed.');
        }

        state.activeRoute = data;
        displayRouteResults(data);
        highlightRouteOnSvg(data);
        showBanner(`Optimal delivery route found! Total travel time: ${data.total_travel_time} minutes.`, 'success');

    } catch (err) {
        console.error('Route error:', err);
        showBanner(`Error: ${err.message}`, 'error');
        clearHighlights();
        dom.resultsPlaceholder.classList.remove('hidden');
        dom.resultsPlaceholder.innerHTML = `<p style="color: var(--color-red-600); font-weight: 600;">❌ ${err.message}</p>`;
        dom.resultsContent.classList.add('hidden');
    } finally {
        setLoadingState(false);
    }
}

// ============================================================
// 6. RESULT DISPLAY & HIGHLIGHTING
// ============================================================
function displayRouteResults(data) {
    dom.resultsPlaceholder.classList.add('hidden');
    dom.resultsContent.classList.remove('hidden');

    // 1. Metric values
    dom.metricTravelTime.textContent = `${data.total_travel_time}m`;
    dom.metricExploredCount.textContent = `${data.explored_nodes ? data.explored_nodes.length : 0}`;
    dom.metricRouteSteps.textContent = `${data.route.length - 1} legs`;

    // 2. Sequence of Route Badges
    dom.optimalPathBadges.innerHTML = '';
    data.route.forEach((nodeId, idx) => {
        const badge = document.createElement('span');
        badge.className = 'path-node-badge';
        badge.textContent = nodeId;
        dom.optimalPathBadges.appendChild(badge);

        if (idx < data.route.length - 1) {
            const arrow = document.createElement('span');
            arrow.className = 'path-arrow';
            arrow.textContent = '→';
            dom.optimalPathBadges.appendChild(arrow);
        }
    });

    // 3. Explored Nodes Chips
    dom.exploredNodesList.innerHTML = '';
    if (data.explored_nodes) {
        data.explored_nodes.forEach(nodeId => {
            const chip = document.createElement('span');
            chip.className = 'explored-chip';
            chip.textContent = nodeId;
            dom.exploredNodesList.appendChild(chip);
        });
    }

    // 4. Leg-by-leg Table Breakdown
    dom.legsTableBody.innerHTML = '';
    if (data.road_segments && data.road_segments.length > 0) {
        data.road_segments.forEach(seg => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${seg.from} &rarr; ${seg.to}</strong></td>
                <td>${state.network ? getRoadName(seg.road_id) : seg.road_id}</td>
                <td><strong>${seg.travel_time} min</strong></td>
            `;
            dom.legsTableBody.appendChild(tr);
        });
    }
}

function getRoadName(roadId) {
    if (!state.network || !state.network.roads) return roadId;
    const r = state.network.roads.find(road => road.id === roadId);
    return r ? r.name : roadId;
}

function highlightRouteOnSvg(data) {
    clearHighlights();

    const { route, explored_nodes, road_segments } = data;
    const { intersections } = state.network;

    // 1. Mark Explored Nodes (amber outline)
    if (explored_nodes) {
        explored_nodes.forEach(nodeId => {
            const g = document.getElementById(`node-group-${nodeId}`);
            if (g) g.classList.add('is-explored');
        });
    }

    // 2. Mark Optimal Nodes (solid green)
    if (route) {
        route.forEach(nodeId => {
            const g = document.getElementById(`node-group-${nodeId}`);
            if (g) {
                g.classList.remove('is-explored');
                g.classList.add('is-optimal');
            }
        });
    }

    // 3. Draw Optimal Path Lines in SVG Route Layer
    dom.routeLayer.innerHTML = '';
    if (road_segments) {
        road_segments.forEach(seg => {
            const u = intersections[seg.from];
            const v = intersections[seg.to];
            if (!u || !v) return;

            const pathLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            pathLine.setAttribute('x1', u.x);
            pathLine.setAttribute('y1', u.y);
            pathLine.setAttribute('x2', v.x);
            pathLine.setAttribute('y2', v.y);
            pathLine.setAttribute('class', 'svg-road-edge optimal-path');
            dom.routeLayer.appendChild(pathLine);
        });
    }
}

function clearHighlights() {
    // Clear route layer lines
    dom.routeLayer.innerHTML = '';

    // Remove classes from node groups
    document.querySelectorAll('.svg-node-group').forEach(g => {
        g.classList.remove('is-explored', 'is-optimal');
    });
}

// ============================================================
// 7. TRAFFIC SIMULATION CONTROL
// ============================================================
async function onUpdateTrafficClick() {
    const roadId = dom.trafficRoadSelect.value;
    const travelTime = parseFloat(dom.trafficTimeInput.value);

    if (!roadId) {
        showBanner('Please select a road to update traffic.', 'error');
        return;
    }

    if (isNaN(travelTime) || travelTime <= 0) {
        showBanner('Travel time must be a valid number greater than 0.', 'error');
        return;
    }

    try {
        showBanner(`Updating traffic on road ${roadId}...`, 'info');
        const res = await fetch(`${state.apiBaseUrl}/api/update-traffic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ road_id: roadId, travel_time: travelTime })
        });

        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.message || 'Failed to update traffic.');
        }

        showBanner(`Traffic updated on road ${roadId}! New travel time: ${travelTime} min.`, 'success');
        
        // Reload network state to update visualization
        await loadNetworkData();

        // If a route was previously calculated, recalculate it automatically
        if (state.activeRoute) {
            dom.btnFindRoute.click();
        }

    } catch (err) {
        console.error('Traffic update error:', err);
        showBanner(`Traffic Error: ${err.message}`, 'error');
    }
}

async function onResetTrafficClick() {
    try {
        showBanner('Resetting all road travel times to base values...', 'info');
        const res = await fetch(`${state.apiBaseUrl}/api/traffic/reset`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.message || 'Failed to reset traffic.');
        }

        showBanner('All road travel times reset to default.', 'success');
        await loadNetworkData();

        // Recalculate route if active
        if (state.activeRoute) {
            dom.btnFindRoute.click();
        }

    } catch (err) {
        console.error('Traffic reset error:', err);
        showBanner(`Reset Error: ${err.message}`, 'error');
    }
}

function updateActiveTrafficList() {
    if (!state.network) return;

    const modifiedRoads = state.network.roads.filter(r => r.is_modified);

    if (modifiedRoads.length === 0) {
        dom.activeTrafficContainer.classList.add('hidden');
        dom.activeTrafficList.innerHTML = '';
        return;
    }

    dom.activeTrafficContainer.classList.remove('hidden');
    dom.activeTrafficList.innerHTML = '';

    modifiedRoads.forEach(r => {
        const li = document.createElement('li');
        li.className = 'traffic-tag-item';
        li.innerHTML = `
            <span><strong>${r.id}</strong>: ${r.current_travel_time}m (Base: ${r.base_travel_time}m)</span>
            <span>Congested</span>
        `;
        dom.activeTrafficList.appendChild(li);
    });
}

// ============================================================
// 8. HELPER UTILITIES
// ============================================================
function showBanner(message, type = 'info') {
    dom.statusMessage.textContent = message;
    dom.statusBanner.className = `status-banner ${type}`;
    dom.statusBanner.classList.remove('hidden');
}

function setLoadingState(isLoading) {
    dom.btnFindRoute.disabled = isLoading;
    const btnSpan = dom.btnFindRoute.querySelector('span');
    if (btnSpan) {
        btnSpan.textContent = isLoading ? 'Calculating A* Route...' : 'Find Optimal Route';
    }
}
