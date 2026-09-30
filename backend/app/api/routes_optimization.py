"""
Optimization execution and telemetry API routes for AdaptIQ-R.

Manages asynchronous evolutionary optimization runs, real-time status polling,
and continuation (adapt) calls.  Each run executes in a background daemon
thread so the FastAPI event loop remains non-blocking.

Background thread design: We deliberately use threading (not asyncio tasks)
because the GA's Dijkstra calls are CPU-bound and would block the event loop
if run as coroutines.  The thread writes to a shared dict protected by GIL
granularity; polling endpoints read this dict asynchronously.

Routes
------
POST /api/optimization/start          — Launch a new GA run in a background thread.
GET  /api/optimization/{id}/status    — Poll live telemetry for a running/completed run.
GET  /api/optimization/{id}/history   — Retrieve per-generation metric history.
POST /api/optimization/{id}/adapt     — Continue an existing run for more generations.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.models import (
    GenerationMetric,
    OptimizationConfig,
    OptimizationState,
)
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.api.routes_scenario import SCENARIOS

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])

# ---------------------------------------------------------------------------
# Global run registries (run_id → object)
# ---------------------------------------------------------------------------
OPTIMIZERS: Dict[str, GeneticAlgorithmOptimizer] = {}
RUN_STATES: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class StartOptimizationRequest(BaseModel):
    """Request body for starting a new Genetic Algorithm optimization run.

    Attributes
    ----------
    scenario_id:
        ID of a previously generated scenario (from POST /api/scenario/generate).
    is_adaptive:
        If ``True``, use AdaptIQ-R mode with Mamdani Fuzzy hyperparameter
        adaptation.  If ``False``, use the fixed-parameter Baseline GA.
    seed:
        Deterministic RNG seed for population initialisation.
    population_size:
        Number of candidate route permutations per generation.
    generations:
        Total number of evolutionary steps to execute.
    initial_mutation_rate:
        Starting mutation probability (overridden each generation in adaptive mode).
    distance_weight:
        Weight on normalised route distance in the fitness formula.
    time_weight:
        Weight on normalised travel time in the fitness formula.
    penalty_weight:
        Weight on constraint-violation penalty in the fitness formula.
    """

    scenario_id: str
    is_adaptive: bool = True
    seed: int = 42
    population_size: int = Field(default=100, ge=10, le=500)
    generations: int = Field(default=150, ge=5, le=1000)
    initial_mutation_rate: float = Field(default=0.15, ge=0.01, le=0.99)
    distance_weight: float = Field(default=0.45, ge=0.0, le=1.0)
    time_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    penalty_weight: float = Field(default=0.20, ge=0.0, le=1.0)


class AdaptOptimizationRequest(BaseModel):
    """Request body for continuing an existing optimization run.

    Attributes
    ----------
    generations:
        Additional generations to execute on top of the already-completed run.
    """

    generations: int = Field(default=80, ge=5, le=500)


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------


def _optimization_worker(run_id: str, generations: int) -> None:
    """Execute GA generations in a daemon background thread.

    Writes live telemetry into ``RUN_STATES[run_id]`` after each generation
    so that polling endpoints can serve near-real-time data to the frontend.

    The thread introduces a 15 ms inter-generation sleep to allow the HTTP
    server sufficient CPU headroom for polling requests during long runs.

    Parameters
    ----------
    run_id:
        Registry key identifying this optimization run.
    generations:
        Number of GA ``step()`` calls to perform.

    Notes
    -----
    Thread safety: The ``RUN_STATES`` dict values are plain Python dicts.
    Writes occur under CPython's GIL so individual key assignments are atomic.
    No additional locking is required for the read-heavy polling pattern.
    """
    opt: GeneticAlgorithmOptimizer = OPTIMIZERS[run_id]
    state: Dict[str, Any] = RUN_STATES[run_id]
    state["status"] = "running"

    try:
        for _ in range(generations):
            # Each step() call: O(N * Dijkstra + S²*L + R*D) — see GA docstring
            metric: GenerationMetric = opt.step()

            # Atomic dict updates — GIL-safe under CPython
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

            # Yield CPU to HTTP polling handlers between generations
            time.sleep(0.015)

        state["status"] = "completed"
    except Exception as exc:  # noqa: BLE001
        state["status"] = "failed"
        state["error_message"] = str(exc)


# ---------------------------------------------------------------------------
# Route handlers (all async for non-blocking FastAPI event loop)
# ---------------------------------------------------------------------------


@router.post("/start", summary="Launch a new GA optimization run")
async def start_optimization(req: StartOptimizationRequest) -> Dict[str, Any]:
    """Launch a Genetic Algorithm optimization run in a background thread.

    Creates a :class:`GeneticAlgorithmOptimizer` instance configured with the
    requested parameters, registers it in the global ``OPTIMIZERS`` registry,
    and starts a daemon background thread.  The caller receives a ``run_id``
    immediately and can poll ``/status`` for live progress.

    Parameters
    ----------
    req:
        Optimization parameters including scenario, GA config, and mode.

    Returns
    -------
    dict
        ``{"run_id": str, "status": "running"}``

    Raises
    ------
    HTTPException (404)
        If the referenced ``scenario_id`` has not been generated yet.
    """
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario_id}' not found.")

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
        penalty_weight=req.penalty_weight,
    )

    disruption_engine = DisruptionEngine(scenario)
    opt = GeneticAlgorithmOptimizer(
        scenario=scenario,
        config=config,
        disruption_engine=disruption_engine,
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
        "error_message": None,
    }

    # Daemon thread — killed automatically when main process exits
    t = threading.Thread(
        target=_optimization_worker,
        args=(run_id, req.generations),
        daemon=True,
    )
    t.start()

    return {"run_id": run_id, "status": "running"}


@router.get("/{run_id}/status", summary="Poll live optimization telemetry")
async def get_optimization_status(run_id: str) -> Dict[str, Any]:
    """Return the current live state of a running or completed optimization run.

    Parameters
    ----------
    run_id:
        Identifier returned by ``POST /api/optimization/start``.

    Returns
    -------
    dict
        Full run state including current generation, best fitness, diversity,
        mutation rate, activated fuzzy rules, and feasibility flag.

    Raises
    ------
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    if run_id not in RUN_STATES:
        raise HTTPException(status_code=404, detail=f"Optimization run '{run_id}' not found.")
    return RUN_STATES[run_id]


@router.get("/{run_id}/history", summary="Retrieve full per-generation metric history")
async def get_optimization_history(run_id: str) -> List[Dict[str, Any]]:
    """Return the ordered list of per-generation metrics for a run.

    Parameters
    ----------
    run_id:
        Identifier returned by ``POST /api/optimization/start``.

    Returns
    -------
    List[dict]
        One dict per completed generation containing fitness statistics,
        diversity, mutation rate, exploration level, and route data.

    Raises
    ------
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    if run_id not in RUN_STATES:
        raise HTTPException(status_code=404, detail=f"Optimization run '{run_id}' not found.")
    return RUN_STATES[run_id]["history"]


@router.post("/{run_id}/adapt", summary="Continue an existing run for more generations")
async def adapt_optimization(run_id: str, req: AdaptOptimizationRequest) -> Dict[str, Any]:
    """Continue a completed or paused optimization run for additional generations.

    Re-uses the existing :class:`GeneticAlgorithmOptimizer` (including its
    current population and history) to avoid cold-start overhead.

    Parameters
    ----------
    run_id:
        Identifier of the run to continue.
    req:
        Number of additional generations to execute.

    Returns
    -------
    dict
        ``{"run_id": str, "status": "running", "target_generations": int}``

    Raises
    ------
    HTTPException (400)
        If the run is already actively running.
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    if run_id not in RUN_STATES or run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail=f"Optimization run '{run_id}' not found.")

    state = RUN_STATES[run_id]
    if state["status"] == "running":
        raise HTTPException(status_code=400, detail="Optimization is already running.")

    state["total_generations"] += req.generations
    t = threading.Thread(
        target=_optimization_worker,
        args=(run_id, req.generations),
        daemon=True,
    )
    t.start()

    return {
        "run_id": run_id,
        "status": "running",
        "target_generations": state["total_generations"],
    }
