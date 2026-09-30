"""
API Integration tests for AdaptIQ-R.
Verifies REST endpoints for scenario generation, optimization, disruptions, and benchmarks.
"""

import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "operational"

    res_h = client.get("/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "healthy"


def test_api_scenario_lifecycle():
    res = client.post("/api/scenario/generate", json={"node_count": 10, "seed": 42})
    assert res.status_code == 200
    scenario = res.json()
    assert scenario["node_count"] == 10
    scenario_id = scenario["id"]

    res_get = client.get(f"/api/scenario/{scenario_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == scenario_id


def test_api_optimization_and_disruption():
    # 1. Generate scenario
    sc_res = client.post("/api/scenario/generate", json={"node_count": 10, "seed": 42})
    scenario = sc_res.json()
    sc_id = scenario["id"]

    # 2. Start optimization
    start_res = client.post("/api/optimization/start", json={
        "scenario_id": sc_id,
        "generations": 15,
        "population_size": 30,
        "is_adaptive": True
    })
    assert start_res.status_code == 200
    run_id = start_res.json()["run_id"]

    # 3. Poll status
    time.sleep(0.4)
    status_res = client.get(f"/api/optimization/{run_id}/status")
    assert status_res.status_code == 200
    status = status_res.json()
    assert status["run_id"] == run_id
    assert status["current_generation"] > 0

    # 4. Inject road-block disruption
    e = scenario["edges"][0]
    dis_res = client.post("/api/disruption/road-block", json={
        "run_id": run_id,
        "source": e["source"],
        "target": e["target"]
    })
    assert dis_res.status_code == 200
    assert dis_res.json()["severity"] > 0.0

    # 5. Adapt continuation
    adapt_res = client.post(f"/api/optimization/{run_id}/adapt", json={"generations": 10})
    # Wait until finished or check status
    time.sleep(0.3)
    hist_res = client.get(f"/api/optimization/{run_id}/history")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) > 0
