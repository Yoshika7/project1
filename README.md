# AdaptIQ-R: Adaptive Route Optimization Under Disruption

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Tests: 19 Passed](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg)]()

> **A Computational Intelligence Research Prototype**  
> *Evolutionary Route Optimization with Online Mamdani Fuzzy Hyperparameter Control and Dynamic Disruption Recovery.*

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [UN SDG Alignment](#2-un-sdg-alignment)
3. [Solution Overview](#3-solution-overview)
4. [System Architecture](#4-system-architecture)
5. [Genetic Algorithm Formulation](#5-genetic-algorithm-formulation)
6. [Pure Python Mamdani Fuzzy Inference Engine](#6-pure-python-mamdani-fuzzy-inference-engine)
7. [Multi-Objective Fitness Evaluation](#7-multi-objective-fitness-evaluation)
8. [Disruption Dynamics & Recovery](#8-disruption-dynamics--recovery)
9. [Baseline GA vs AdaptIQ-R Comparison](#9-baseline-ga-vs-adaptiq-r-comparison)
10. [REST API Reference](#10-rest-api-reference)
11. [Performance Metrics & Diagnostics](#11-performance-metrics--diagnostics)
12. [Installation & Prerequisites](#12-installation--prerequisites)
13. [Running the Backend API](#13-running-the-backend-api)
14. [Running the Frontend Dashboard](#14-running-the-frontend-dashboard)
15. [Running Reproducible Experiments & Benchmarks](#15-running-reproducible-experiments--benchmarks)
16. [Scientific Reproducibility Guarantees](#16-scientific-reproducibility-guarantees)
17. [Track Innovations](#17-track-innovations)
18. [Current Limitations & Research Roadmap](#18-current-limitations--research-roadmap)



---

## 1. Problem Statement

Vehicle routing problems (VRP) and traveling salesperson formulations in the real world operate under unpredictable physical environments. Conventional static optimizers compute route sequences based on static distance matrices. When sudden events happen—such as unexpected road closures, localized traffic congestion, priority customer changes, or fleet capacity reductions—static schedules fail.

Re-running full global optimization from scratch incurs high latency, discards valuable structural knowledge in the existing route, and can lead to severe schedule thrashing. Conversely, naive evolutionary algorithms with fixed operator probabilities often suffer from:
* **Premature convergence**: Population diversity collapses into local minima before finding alternative detours.
* **Slow disruption recovery**: Fixed low mutation rates cannot inject sufficient structural entropy to escape invalid topological basins when a critical bridge or road is severed.

**AdaptIQ-R** addresses this challenge by introducing an online feedback-controlled evolutionary framework where a **Mamdani Fuzzy Inference System** dynamically adapts genetic operators in response to population state and real-time environmental disruption telemetry.

> 📄 See the full formal problem specification: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md)

---

## 2. UN SDG Alignment

AdaptIQ-R directly contributes to four United Nations Sustainable Development Goals:

| SDG | Goal | AdaptIQ-R Contribution |
|:----|:-----|:----------------------|
| 🏙️ **SDG 11** | Sustainable Cities and Communities | Optimal adaptive routing reduces urban fleet emissions and congestion |
| 🌍 **SDG 13** | Climate Action | Minimising total route distance reduces vehicle CO₂ output per delivery |
| 🏗️ **SDG 9** | Industry, Innovation and Infrastructure | Disruption recovery ensures supply-chain continuity under infrastructure failures |
| 💊 **SDG 3** | Good Health and Well-Being | Priority-aware routing guarantees high-urgency deliveries (medical, food) reach recipients first |



## 2. Solution Overview

AdaptIQ-R couples a permutation-based Genetic Algorithm with an online Fuzzy Controller operating in a closed loop:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ADAPTIQ-R RESEARCH LOOP                         │
└────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  Population P   │◄─────────────────────────────────────────────┐
    └────────┬────────┘                                              │
             │                                                       │
             ▼                                                       │
   [Fitness Evaluation] (Dijkstra + Multi-Objective Weighted Sum)    │
             │                                                       │
             ▼                                                       │
  [Population Diversity, Improvement Rate, Disruption Severity]      │
             │                                                       │
             ▼                                                       │
┌─────────────────────────┐                                          │
│ Mamdani Fuzzy Engine    │                                          │
│ (Tri/Trap MFs, Min/Max) │                                          │
└────────────┬────────────┘                                          │
             │  Output: Mutation Rate [0.05, 0.45]                   │
             │          Exploration Level [0.10, 0.90]               │
             ▼                                                       │
  [Tournament Selection] (Dynamic selection pressure)                │
             │                                                       │
             ▼                                                       │
  [Order Crossover (OX)]                                             │
             │                                                       │
             ▼                                                       │
[Adaptive Swap Mutation] (Scale-directed permutation perturbation)   │
             │                                                       │
             ▼                                                       │
    ┌─────────────────┐                                              │
    │ Population P+1  │──────────────────────────────────────────────┘
    └─────────────────┘
```

The optimizer detects disruptions immediately via graph-level telemetry, re-evaluates the population, and uses fuzzy adaptation to dynamically alter its exploratory behavior without requiring human tuning.

---

## 3. System Architecture

AdaptIQ-R is built with strict separation of concerns across four independent layers:

```
 adaptiq-r/
 ├── backend/app/
 │   ├── core/           # Pydantic data schemas, configs, default weights
 │   ├── simulation/     # MST+kNN road network generator, disruption engines, traffic
 │   ├── optimizer/      # GA operators (OX, Swap, Tournament), Dijkstra routing, fitness
 │   ├── fuzzy/          # Pure Python Mamdani inference, membership functions, 9 rules
 │   ├── evaluation/     # Diversity metrics, benchmark harness, experiment exporters
 │   └── api/            # FastAPI REST endpoints & background thread executors
 ├── frontend/           # Modern React 18 + Vite + Tailwind/Custom CSS + Recharts UI
 ├── experiments/        # CLI reproducible benchmark runners & demo scripts
 └── tests/              # 19 comprehensive unit & integration tests
```

* **Computational Intelligence Engine**: Self-contained Python modules with zero dependency on UI or API code.
* **Simulation Engine**: Generates connected, planar-like synthetic networks using Euclidean coordinates, Kruskal's MST (guaranteeing connectivity), and $k$-nearest neighbors.
* **Backend API**: Asynchronous FastAPI endpoints executing optimizations in worker threads with thread-safe telemetry polling.
* **Frontend UI**: Modular React SPA that visualizes road networks, live convergence curves, and fuzzy rule activation states. Can be swapped for alternative UIs without touching backend code.

---

## 4. Genetic Algorithm Formulation

### 4.1 Chromosome Representation
* Chromosomes are ordered permutations of customer node IDs: $\mathbf{c} = [c_1, c_2, \dots, c_{n-1}]$.
* The depot node ($0$) is explicitly anchored at the beginning and termination of all physical routes during fitness decoding: $[0, c_1, c_2, \dots, c_{n-1}, 0]$.

### 4.2 Genetic Operators
* **Selection**: Tournament Selection with dynamic tournament size $k = \max(2, \lfloor 2 + 3(1 - \text{exploration}) \rfloor)$, ensuring gentle selection during high exploration and intense exploitation during convergence.
* **Elitism**: Best individual is strictly preserved across generations without mutation.
* **Crossover**: Order Crossover (OX-1) preserves the relative order and subset adjacency of customer visits without producing duplicate customer visits.
* **Mutation**: Adaptive Swap Mutation. The number of simultaneous customer swaps per mutated individual scales with the fuzzy exploration output:
  $$k_{\text{swaps}} = \max\left(1, \lfloor 1 + 3 \cdot \text{exploration\_level} \rfloor\right)$$

---

## 5. Pure Python Mamdani Fuzzy Inference Engine

AdaptIQ-R implements a complete Mamdani fuzzy system **from scratch** with no third-party fuzzy libraries.

### 5.1 Linguistic Variables and Term Sets

| Variable | Type | Universe | Terms |
| :--- | :--- | :--- | :--- |
| **Diversity** | Input | $[0.0, 1.0]$ | LOW, MED, HIGH |
| **Improvement** | Input | $[0.0, 1.0]$ | LOW, MED, HIGH |
| **Severity** | Input | $[0.0, 1.0]$ | LOW, MED, HIGH |
| **Mutation Rate** | Output | $[0.05, 0.45]$ | LOW, MED, HIGH |
| **Exploration Level**| Output | $[0.10, 0.90]$ | LOW, MED, HIGH |

### 5.2 Membership Functions
* **Triangular**:
  $$\mu(x; a, b, c) = \max\left(0, \min\left(\frac{x - a}{b - a}, \frac{c - x}{c - b}\right)\right)$$
* **Trapezoidal**:
  $$\mu(x; a, b, c, d) = \max\left(0, \min\left(\frac{x - a}{b - a}, 1, \frac{d - x}{d - b}\right)\right)$$

### 5.3 Fuzzy Rule Base (9 Core Rules)
1. **R1**: IF Diversity is LOW AND Improvement is LOW THEN Mutation is HIGH, Exploration is HIGH
2. **R2**: IF Diversity is LOW AND Improvement is MED THEN Mutation is HIGH, Exploration is MED
3. **R3**: IF Diversity is HIGH AND Improvement is HIGH THEN Mutation is LOW, Exploration is LOW
4. **R4**: IF Disruption is HIGH THEN Mutation is HIGH, Exploration is HIGH
5. **R5**: IF Disruption is MED AND Improvement is LOW THEN Mutation is HIGH, Exploration is MED
6. **R6**: IF Disruption is LOW AND Improvement is HIGH THEN Mutation is LOW, Exploration is LOW
7. **R7**: IF Diversity is MED AND Improvement is MED THEN Mutation is MED, Exploration is MED
8. **R8**: IF Diversity is HIGH AND Improvement is LOW THEN Mutation is MED, Exploration is LOW
9. **R9**: IF Disruption is LOW AND Diversity is LOW THEN Mutation is MED, Exploration is MED

### 5.4 Implication, Aggregation, and Defuzzification
* **Implication**: Mamdani minimum: $\mu_{\text{consequent}}'(y) = \min(\alpha_{\text{rule}}, \mu_{\text{consequent}}(y))$
* **Aggregation**: Maximum operator over all activated rules: $\mu_{\text{agg}}(y) = \max_i \mu_i'(y)$
* **Defuzzification**: Centroid method over 100 discrete sampling intervals:
  $$y^* = \frac{\int y \cdot \mu_{\text{agg}}(y) \, dy}{\int \mu_{\text{agg}}(y) \, dy}$$

---

## 6. Multi-Objective Fitness Evaluation

Fitness evaluates the real physical cost of executing a sequence in the road network:

$$F(\mathbf{c}) = w_d D(\mathbf{c}) + w_t T(\mathbf{c}) + w_p P(\mathbf{c}) + w_c C(\mathbf{c}) + \text{Infeasibility Penalty}$$

Where:
* $D(\mathbf{c})$: Total distance traversed via shortest path Dijkstra graph navigation.
* $T(\mathbf{c})$: Total travel time accounting for dynamic edge traffic factors: $t_e = \frac{\text{length}_e}{\text{speed}_e} \cdot \text{traffic}_e$.
* $P(\mathbf{c})$: Delivery priority delay penalty for high-priority customers visited late in the sequence.
* $C(\mathbf{c})$: Vehicle capacity overflow penalty.
* **Infeasibility Handling**: Severed or unreachable paths receive an immediate $10^6$ penalty, guiding the evolutionary search back to feasible graph topologies.

---

## 7. Disruption Dynamics & Recovery

AdaptIQ-R handles four distinct classes of environmental disruption:

1. **Road Block**: An edge $(u, v)$ is completely severed ($P_{\text{traverse}} = \infty$). The optimizer detects the severance, invalidates cached shortest paths, and invokes `notify_disruption()`.
2. **Traffic Surge**: Edge congestion multiplies travel time by factor $\gamma \in [1.5, 5.0]$.
3. **Priority Shift**: Urgent delivery updates elevate a customer's priority weighting, penalizing late visit orders.
4. **Vehicle Failure**: Fleet capacity drops by $\Delta C$, requiring tighter load constraints.

Disruption Severity is computed objectively:
$$S = 0.40 \cdot \frac{|\text{Edges}_{\text{blocked}}|}{|\text{Edges}|} + 0.30 \cdot \frac{\Delta \text{Traffic}}{\text{Traffic}_{\max}} + 0.15 \cdot \frac{\Delta \text{Priority}}{\text{Priority}_{\max}} + 0.15 \cdot \frac{\Delta \text{Capacity}}{\text{Capacity}_0}$$

---

## 8. Baseline GA vs AdaptIQ-R Comparison

| Feature | Standard Baseline GA | AdaptIQ-R |
| :--- | :--- | :--- |
| **Mutation Rate** | Static ($0.15$) | Dynamic Fuzzy Adaptation ($[0.05, 0.45]$) |
| **Exploration Control** | None (uniform swaps) | Adaptive scale ($[0.10, 0.90]$) |
| **Selection Pressure** | Constant tournament ($k=3$) | Adaptive pressure ($k \in [2, 5]$) |
| **Disruption Reaction** | Unaware, slow drift | Instantaneous severity response |
| **Post-Disruption Recovery** | Susceptible to local trap | Rule R4 spikes entropy to escape trap |

---

## 9. Performance Metrics & Diagnostics

The evaluation engine computes and logs:
* **Population Diversity**: Mean pairwise normalized permutation distance:
  $$\text{Div} = \frac{1}{\binom{N}{2}} \sum_{i < j} \frac{d_H(\mathbf{c}_i, \mathbf{c}_j)}{L}$$
* **Fitness Improvement Rate**: Exponential moving average of best fitness change over a 5-generation rolling window.
* **Recovery Generations**: The number of generations elapsed post-disruption before fitness returns within 5% of pre-disruption baseline.

---

## 10. Installation & Prerequisites

### Prerequisites
* **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14
* **Node.js**: v18+ (for frontend web dashboard)

### Setup Backend
```bash
# Clone the repository
git clone https://github.com/your-username/adaptiq-r.git
cd adaptiq-r

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

---

## 11. Running the Backend API

Start the FastAPI application:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at:
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

---

## 12. Running the Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

The frontend includes 7 interactive research views:
1. **Dashboard**: Live system status and workflow overview.
2. **Scenario Builder**: Interactive SVG graph generation with configurable seeds.
3. **Optimizer**: Real-time convergence curves, route plotting, and live metrics.
4. **Disruption Lab**: Injection controls for road blocks, surges, and vehicle failures.
5. **Side-by-Side Comparison**: Synchronous comparative runs of Baseline GA vs AdaptIQ-R.
6. **Analytics**: Deep parameter logging and diversity decay curves.
7. **Benchmark Suite**: Multi-seed statistical verification suite.

---

## 13. Running Reproducible Experiments & Benchmarks

### Execute the Standalone Demo Script
Runs an end-to-end 20-node scenario, injects a road block disruption, recovers the route, and exports structured JSON results:
```bash
python -m experiments.demo
```

### Run Full Test Suite
Verify mathematical correctness of all fuzzy membership functions, crossover operators, and Dijkstra rerouting:
```bash
python -m pytest tests/ -v
```

---

## 14. Scientific Reproducibility Guarantees

* **Deterministic Seed Control**: Supplying an integer seed produces identical node positions, connectivity graphs, customer demands, and initial populations across different environments.
* **No Synthetic Mocking**: All fitness metrics, diversity scores, defuzzified mutation rates, and recovery benchmarks are calculated by the algorithmic engines.
* **Unbiased Baseline**: The Baseline GA uses identical tournament selection, crossover, and fitness scoring. When AdaptIQ-R out- or underperforms, it is reported transparently.

---

## 18. Current Limitations & Research Roadmap

* **Single-Depot Architecture**: Current formulation models single-depot routing. Future work includes multi-depot and heterogeneous vehicle fleets.
* **Time Windows (VRPTW)**: Next iterations will introduce strict customer time-window constraints into the fuzzy penalty calculation.
* **Type-2 Fuzzy Inference**: Exploring Interval Type-2 Fuzzy Logic to handle uncertainty in disruption sensor noise.
* **Large-Scale Hierarchical Graphs**: Adding clustering pre-processors for networks exceeding 500 nodes.

---

## REST API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/api/scenario/generate` | Generate a synthetic road network scenario |
| `GET` | `/api/scenario/{id}` | Retrieve a specific scenario by ID |
| `POST` | `/api/optimize/start` | Start an optimization run (returns run_id) |
| `GET` | `/api/optimize/{run_id}/status` | Poll current optimization status and latest metrics |
| `POST` | `/api/optimize/{run_id}/step` | Execute a single GA generation step |
| `POST` | `/api/disrupt/{run_id}/block` | Apply a road block disruption |
| `POST` | `/api/disrupt/{run_id}/surge` | Apply a traffic surge disruption |
| `POST` | `/api/disrupt/{run_id}/vehicle` | Simulate a vehicle failure |
| `GET` | `/api/benchmark/run` | Run the full multi-seed benchmark suite |
| `GET` | `/health` | Health check endpoint |

Interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Track Innovations

AdaptIQ-R contributes 6 novel technical innovations at the intersection of computational intelligence, evolutionary computation, and dynamic logistics optimisation.

**Key highlights:**
1. **Online Mamdani FIS for VRP** — First coupling of Mamdani fuzzy adaptation to dynamic VRP disruption recovery in open literature
2. **Disruption Severity as FIS Input** — Domain-specific telemetry enables proactive (not reactive) adaptation
3. **Exploration-Scaled Tournament Pressure** — Coordinated mutation + selection pressure via a single FIS output
4. **Adaptive Multi-Swap Mutation** — Structural magnitude adaptation vs probability-only classical approaches
5. **Infeasibility-Tolerant Fitness** — Preserves genetic diversity during severe disruption recovery
6. **Zero-Dependency Pure Python FIS** — Full mathematical transparency, no scikit-fuzzy or MATLAB dependency

> 📄 Full innovation details with mathematical formulation and prior-work comparison: [INNOVATIONS.md](INNOVATIONS.md)

---

## Supporting Documentation

| Document | Purpose |
|:---------|:--------|
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | Formal problem definition, inputs/outputs, SDG alignment, failure analysis |
| [INNOVATIONS.md](INNOVATIONS.md) | 6 novel contributions with math, novelty justification, prior-work comparison |
| [AdaptIQ_R_Research_Notebook.ipynb](AdaptIQ_R_Research_Notebook.ipynb) | Self-contained Jupyter research notebook |
| [streamlit_app.py](streamlit_app.py) | Interactive Streamlit web demo |

