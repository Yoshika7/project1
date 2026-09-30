"""
Optimization execution and telemetry API routes.
Runs evolutionary searches asynchronously in background threads to support real-time polling.
"""

import threading
import time
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.core.models import (
    OptimizationConfig,
    OptimizationState,
    GenerationMetric
)
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.api.routes_scenario import SCENARIOS

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])

# Global run registry
OPTIMIZERS: Dict[str, GeneticAlgorithmOptimizer] = {}
RUN_STATES: Dict[str, Dict[str, Any]] = {}


class StartOptimizationRequest(BaseModel):
    scenario_id: str
    is_adaptive: bool = True
    seed: int = 42
    population_size: int = 100
    generations: int = 150
    initial_mutation_rate: float = 0.15
    distance_weight: float = 0.45
    time_weight: float = 0.35
    penalty_weight: float = 0.20


class AdaptOptimizationRequest(BaseModel):
    generations: int = Field(default=80, ge=5, le=500)


def _optimization_worker(run_id: str, generations: int):
    opt = OPTIMIZERS[run_id]
    state = RUN_STATES[run_id]
    state["status"] = "running"

    try:
        for _ in range(generations):
            metric = opt.step()
            state["current_generation"] = metric.generation
            state["best_fitness"] = metric.best_fitness
            state["best_route"] = metric.best_route
            state["detailed_path"] = metric.detailed_path
            state["diversity"] = metric.population_diversity
            state["mutation_rate"] = metric.mutation_rate
            state["exploration_level"] = metric.exploration_level
            state["disruption_severity"] = metric.disruption_severity
            state["activated_rules"] = metric.activated_rules
            state["is_feasible"] = metric.is_feasible
            state["total_distance"] = metric.total_distance
            state["total_travel_time"] = metric.total_travel_time
            state["history"].append(metric.model_dump())

            # Small delay so browser has ample time to poll generation-by-generation
            time.sleep(0.015)

        state["status"] = "completed"
    except Exception as e:
        state["status"] = "failed"
        state["error_message"] = str(e)


@router.post("/start")
def start_optimization(req: StartOptimizationRequest):
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = SCENARIOS[req.scenario_id]
    run_id = f"opt_{uuid.uuid4().hex[:8]}"

    config = OptimizationConfig(
        seed=req.seed,
        population_size=req.population_size,
        generations=req.generations,
        is_adaptive=req.is_adaptive,
        initial_mutation_rate=req.initial_mutation_rate,
        distance_weight=req.distance_weight,
        time_weight=req.time_weight,
        penalty_weight=req.penalty_weight
    )

    disruption_engine = DisruptionEngine(scenario)
    opt = GeneticAlgorithmOptimizer(
        scenario=scenario,
        config=config,
        disruption_engine=disruption_engine
    )

    OPTIMIZERS[run_id] = opt
    RUN_STATES[run_id] = {
        "run_id": run_id,
        "status": "pending",
        "scenario_id": req.scenario_id,
        "is_adaptive": req.is_adaptive,
        "current_generation": 0,
        "total_generations": req.generations,
        "best_fitness": float("inf"),
        "best_route": [],
        "detailed_path": [],
        "diversity": 0.0,
        "mutation_rate": req.initial_mutation_rate,
        "exploration_level": 0.5,
        "disruption_severity": 0.0,
        "activated_rules": [],
        "is_feasible": True,
        "total_distance": 0.0,
        "total_travel_time": 0.0,
        "history": [],
        "error_message": None
    }

    t = threading.Thread(target=_optimization_worker, args=(run_id, req.generations), daemon=True)
    t.start()

    return {"run_id": run_id, "status": "running"}


@router.get("/{run_id}/status")
def get_optimization_status(run_id: str):
    if run_id not in RUN_STATES:
        raise HTTPException(status_code=404, detail="Optimization run not found")
    return RUN_STATES[run_id]


@router.get("/{run_id}/history")
def get_optimization_history(run_id: str):
    if run_id not in RUN_STATES:
        raise HTTPException(status_code=404, detail="Optimization run not found")
    return RUN_STATES[run_id]["history"]


@router.post("/{run_id}/adapt")
def adapt_optimization(run_id: str, req: AdaptOptimizationRequest):
    if run_id not in RUN_STATES or run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail="Optimization run not found")

    state = RUN_STATES[run_id]
    if state["status"] == "running":
        raise HTTPException(status_code=400, detail="Optimization is already currently running")

    state["total_generations"] += req.generations
    t = threading.Thread(target=_optimization_worker, args=(run_id, req.generations), daemon=True)
    t.start()

    return {"run_id": run_id, "status": "running", "target_generations": state["total_generations"]}
