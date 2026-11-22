# SmartRoute – Intelligent Delivery Route Optimization Using A* Search Algorithm

An AI-powered web-based delivery route optimization system developed as a college AI mini-project. The system calculates the minimum travel-time path between a central warehouse and delivery destinations across an urban road network in Tumakuru, Karnataka, using the **A\* Search Algorithm** with an admissible and consistent Euclidean distance heuristic.

---

## 📋 Table of Contents
1. [Project Introduction](#-project-introduction)
2. [Problem Statement](#-problem-statement)
3. [Objectives](#-objectives)
4. [Technology Stack](#-technology-stack)
5. [System Architecture & Workflow](#-system-architecture--workflow)
6. [A* Search Algorithm In-Depth](#-a-search-algorithm-in-depth)
7. [Heuristic Function, Admissibility & Consistency](#-heuristic-function-admissibility--consistency)
8. [Installation & Setup Guide](#-installation--setup-guide)
9. [Running the Application](#-running-the-application)
10. [Automated Test Suites](#-automated-test-suites)
11. [Screenshots to Capture for the Project Report](#-screenshots-to-capture-for-the-project-report)
12. [Possible Viva Questions and Answers](#-possible-viva-questions-and-answers)

---

## 📖 Project Introduction
Last-mile delivery logistics face recurring challenges from road congestion, detours, and variable traffic delays. Traditional unguided search algorithms like Breadth-First Search (BFS) or Depth-First Search (DFS) either explore an impractical number of nodes or fail to find optimal paths in weighted networks. While Dijkstra's algorithm (Uniform Cost Search) guarantees optimality, it expands radially in all directions without target orientation.

**SmartRoute** implements the **A\* Search Algorithm**, which introduces heuristic guidance to direct search towards the destination. Built using a Python Flask backend and an interactive SVG frontend, SmartRoute simulates dynamic traffic conditions in Tumakuru and demonstrates real-time optimal rerouting.

---

## 🎯 Problem Statement
Given a set of delivery destinations in an urban road network with varying road lengths and travel-time costs, design and implement an intelligent pathfinding application that:
1. Models an urban road network with realistic coordinates and bidirectional travel costs.
2. Identifies the quickest delivery route between a distribution warehouse and target destinations.
3. Adapts dynamically to traffic congestion without requiring third-party paid APIs, GPS hardware, or machine learning models.
4. Provides clear visual feedback on node exploration, road travel times, and path metrics.

---

## 🎯 Objectives
- **A\* Implementation**: Implement an authentic A\* search using a binary heap (`heapq`) priority queue.
- **Mathematically Sound Heuristic**: Formulate an admissible ($h \le h^*$) and consistent ($h(n) \le c(n,n') + h(n')$) straight-line travel-time heuristic.
- **Traffic Simulation**: Allow users to adjust road travel times in real time to observe dynamic route replanning.
- **Interactive Visualization**: Render the entire graph using pure Scalable Vector Graphics (SVG) without complex frontend frameworks.
- **Zero Third-Party External Dependencies**: Run purely on Python Flask and Vanilla HTML/CSS/JavaScript.

---

## 💻 Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3 + Flask 3.1 | REST API routing, request validation, template serving |
| **Search Algorithm** | A\* Search Algorithm | Priority queue (`heapq`) based minimum travel-time pathfinding |
| **Dataset & Storage** | JSON (`road_network.json`) | Graph representation (12 intersections, 18 bidirectional roads) |
| **Frontend UI** | HTML5, CSS3 | Clean, modern light interface with Navy and Emerald Green accents |
| **Client Logic** | Vanilla JavaScript (ES6) | Asynchronous Fetch API, DOM manipulation, state management |
| **Map Rendering** | SVG (Scalable Vector Graphics) | Vector-based interactive visualization of nodes, edges, and paths |

---

## 🏗️ System Architecture & Workflow

```text
[ Browser / Frontend Client ]
       │
       ├── 1. GET /api/network ───────────► [ Flask Backend (app.py) ]
       │◄── JSON (nodes, roads, costs) ───┤          │
       │                                             │ loads
       ├── 2. Render SVG Network                     ▼
       │                                     [ data/network.py ]
       ├── 3. User Selects Source & Dest             │ parses
       │                                             ▼
       ├── 4. POST /api/find-route ──────► [ data/road_network.json ]
       │◄── Optimal Route + Metrics ──────┤          │
       │                                             │ builds graph
       ├── 5. Highlight Green Path & Explored Nodes  ▼
       │                                     [ backend/astar.py ]
       └── 6. Optional: Modify Traffic ──► (Priority Queue + Heuristic)
```

### Complete Execution Steps:
1. **Application Launch**: Flask serves `index.html` and static assets.
2. **Network Initialization**: Frontend calls `GET /api/network`. Node coordinates `(x, y)` and road weights are drawn on the SVG canvas.
3. **Route Planning Request**: User chooses a source (e.g. `A - Warehouse`) and destination (e.g. `L - Hub`). Clicking **Find Optimal Route** dispatches a `POST /api/find-route` JSON request.
4. **Graph Construction**: The backend builds an adjacency list with active traffic costs.
5. **A\* Search Execution**: Nodes are evaluated via $f(n) = g(n) + h(n)$ using a priority queue until the goal node is reached.
6. **Path Reconstruction**: Backtracks via parent pointers to generate the ordered list of nodes and road segments.
7. **Client Rendering**: Frontend updates statistics, highlights the green route, and marks explored nodes with amber outlines.
8. **Traffic Adjustment**: When a road's travel time is updated via `POST /api/update-traffic`, the server updates the edge weight, the SVG displays a red dashed line, and A\* calculates a new optimal detour.

---

## 🧮 A* Search Algorithm In-Depth

A\* search evaluates candidate nodes using the evaluation function:

$$\mathbf{f(n) = g(n) + h(n)}$$

- **$g(n)$ (Exact Path Cost)**: The cumulative travel time (in minutes) spent travelling from the starting warehouse to node $n$ along the currently evaluated path.
- **$h(n)$ (Heuristic Estimate)**: The estimated travel time remaining from node $n$ to the delivery destination.
- **$f(n)$ (Total Estimated Cost)**: The projected total travel time of the cheapest complete delivery route passing through node $n$.

### Step-by-Step Search Logic:
1. Push the start node to the open set (priority queue) with $f(\text{start}) = 0 + h(\text{start}, \text{goal})$.
2. While the open set is not empty:
   - Pop node $n$ having the lowest $f(n)$.
   - If $n == \text{goal}$, terminate and reconstruct the optimal route.
   - Add $n$ to the closed set (explored nodes).
   - For every neighbor $n'$ of $n$:
     - Compute tentative actual cost: $g_{\text{tentative}} = g(n) + \text{cost}(n, n')$.
     - If $g_{\text{tentative}} < g(n')$:
       - Update parent pointer: $\text{parent}[n'] = n$.
       - Set $g(n') = g_{\text{tentative}}$.
       - Calculate $f(n') = g(n') + h(n', \text{goal})$.
       - Push $n'$ into the priority queue.

---

## 📐 Heuristic Function, Admissibility & Consistency

### Heuristic Formulation
The heuristic converts straight-line Euclidean distance into travel time using a theoretical upper bound vehicle speed ($V_{\max} = 40.0\text{ units/min}$):

$$h(n) = \frac{\sqrt{(x_{\text{goal}} - x_n)^2 + (y_{\text{goal}} - y_n)^2}}{V_{\max}}$$

### 1. Admissibility Condition: $h(n) \le h^*(n)$
- A heuristic is **admissible** if it never overestimates the true remaining cost $h^*(n)$ to reach the destination.
- **Proof**: A straight line is the shortest physical distance between two points in 2D space ($\text{Euclidean} \le \text{Actual Road Distance}$). Because $V_{\max}$ is the maximum possible travel speed, dividing the shortest distance by the highest speed yields the absolute minimum possible travel time. Therefore, $h(n)$ is strictly lower than or equal to the actual road travel time.
- **Result**: Guarantees that A\* will never return a suboptimal path.

### 2. Consistency (Monotonicity) Condition: $h(n) \le c(n, n') + h(n')$
- A heuristic is **consistent** if the estimated cost from node $n$ to the goal is no greater than the step cost from $n$ to neighbor $n'$ plus the estimated cost from $n'$ to the goal.
- **Proof**: By the triangle inequality of Euclidean space:
  $$\text{dist}(n, \text{goal}) \le \text{dist}(n, n') + \text{dist}(n', \text{goal})$$
  Dividing all terms by the constant positive scalar $V_{\max}$:
  $$\frac{\text{dist}(n, \text{goal})}{V_{\max}} \le \frac{\text{dist}(n, n')}{V_{\max}} + \frac{\text{dist}(n', \text{goal})}{V_{\max}}$$
  $$h(n) \le \text{minimum\_time}(n, n') + h(n') \le \text{cost}(n, n') + h(n')$$
- **Result**: Once a node is expanded from the priority queue, the shortest path to it has been discovered. Nodes are never re-opened.

---

## 📦 Installation & Setup Guide

### System Requirements
- Windows, macOS, or Linux
- Python 3.10, 3.11, 3.12, or 3.13 installed
- Any modern web browser (Google Chrome, Microsoft Edge, Firefox, Safari)

### Step 1: Open Terminal in Project Folder
```powershell
cd d:\SmartRoute-Intelligent-Delivery-Route-Optimization-
```

### Step 2: Create & Activate Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt `cmd`):**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```
*(Only installs Flask; no heavy third-party packages required).*

---

## 🚀 Running the Application

### Start the Server
With your virtual environment active, run:
```powershell
python app.py
```

### Access the Web Interface
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Automated Test Suites

Run any of the 4 included test suites to verify functionality:

```powershell
# 1. A* Algorithm Tests (Admissibility, Consistency, Routing)
python test_astar.py

# 2. REST API Endpoint Tests (CORS, Request Validation, Error Handling)
python test_backend_api.py

# 3. End-to-End Integration Tests (Frontend-to-Backend HTTP Contract)
python test_integration.py

# 4. Phase 6 Benchmark (A* vs UCS Optimality across all 132 pairs)
python test_phase6_validation.py
```

---

## 📸 Screenshots to Capture for the Project Report

When preparing your project report and slide deck, include the following screenshots:

1. **Dashboard Overview (Default State)**:
   - Full webpage showing the navigation header, route dropdowns, clean SVG road network of Tumakuru, and academic theory section.
2. **Optimal Path Calculation (A $\rightarrow$ L)**:
   - Showing the green highlighted route `A → B → E → G → K → L`, travel time metric (`22.0 min`), and explored node chips.
3. **Traffic Congestion Simulation**:
   - Selecting road `B-E`, adding `+15 min (Jam)`, showing the red dashed road style and warning badge.
4. **Dynamic Rerouting Response**:
   - Showing how A\* reroutes around congestion through the Central corridor `A → B → D → J → I → L` (`23.0 min`).
5. **Interactive Node/Road Hover Inspection**:
   - Hovering over an intersection or edge showing tooltip metadata (coordinates, landmark name, road travel time).
6. **Terminal / Console Test Execution**:
   - Terminal window showing passing results from `python test_phase6_validation.py`.

---

## 🎓 Possible Viva Questions and Answers

### Q1: What is the primary difference between Dijkstra's Algorithm and A* Search?
**Answer**: Dijkstra's algorithm (Uniform Cost Search) expands radially based solely on the actual distance from the start $g(n)$, with no knowledge of where the destination lies. A\* incorporates a heuristic estimate $h(n)$ ($f(n) = g(n) + h(n)$) to guide the search toward the destination, reducing the number of explored nodes while maintaining optimality.

### Q2: What does it mean for a heuristic to be admissible?
**Answer**: A heuristic $h(n)$ is admissible if it never overestimates the true minimum cost to reach the goal ($h(n) \le h^*(n)$ for all nodes). It ensures A\* will find the optimal solution.

### Q3: Why is straight-line Euclidean distance divided by maximum speed admissible in our project?
**Answer**: A straight line is the shortest geometric distance between two points in Euclidean space. By dividing this minimum distance by the upper bound on vehicle speed ($V_{\max} = 40.0\text{ units/min}$), the estimated travel time is mathematically guaranteed to be less than or equal to the actual driving time on road segments.

### Q4: What is heuristic consistency (monotonicity)?
**Answer**: A heuristic is consistent if for every node $n$ and neighbor $n'$, $h(n) \le \text{cost}(n, n') + h(n')$. Consistency guarantees that $f(n)$ values along any path are non-decreasing and that once a node is expanded from the priority queue, the shortest path to it has already been found.

### Q5: How does the priority queue work in A* search?
**Answer**: The priority queue (implemented using Python's min-heap `heapq`) stores candidate nodes ordered by their total evaluation score $f(n) = g(n) + h(n)$. The algorithm always pops the node with the lowest estimated total travel time first.

### Q6: How does the system adapt when a user adds traffic to a road?
**Answer**: When traffic is modified via the API, the edge weight for that road increases. On recalculation, the actual cost $g(n)$ along the congested corridor becomes higher, causing the priority queue to explore alternative paths where $f(n)$ remains lower, resulting in an optimal detour.

### Q7: Why did we choose SVG instead of HTML Canvas or Google Maps API?
**Answer**: SVG uses vector XML elements (`<line>`, `<circle>`, `<text>`) that can be styled via CSS and inspected in the DOM. It requires no paid API keys, runs offline, scales crisply to any screen resolution, and keeps the project self-contained.

### Q8: What data structure represents the road network?
**Answer**: An **Adjacency List** stored in a Python dictionary. Each intersection key maps to a list of edge objects containing the neighbor ID, travel time cost, and road ID.
