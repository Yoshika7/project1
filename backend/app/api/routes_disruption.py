"""
Disruption injection API routes.
Applies real physical changes to the routing environment and computes quantitative severity.
"""

from typing import List, Tuple, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.models import DisruptionSeverity
from backend.app.api.routes_optimization import OPTIMIZERS, RUN_STATES
from backend.app.api.routes_scenario import SCENARIOS

router = APIRouter(prefix="/api/disruption", tags=["Disruption"])


class RoadBlockRequest(BaseModel):
    run_id: str
    source: int
    target: int
    description: Optional[str] = None


class TrafficSurgeRequest(BaseModel):
    run_id: str
    edges: List[Tuple[int, int]]
    factor: float = Field(default=2.5, ge=1.0, le=5.0)
    description: Optional[str] = None


class PriorityChangeRequest(BaseModel):
    run_id: str
    node_id: int
    new_priority: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None


class VehicleFailureRequest(BaseModel):
    run_id: str
    capacity_loss_fraction: float = Field(default=0.5, ge=0.1, le=1.0)
    description: Optional[str] = None


@router.post("/road-block", response_model=DisruptionSeverity)
def block_road_endpoint(req: RoadBlockRequest):
    if req.run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail="Optimizer run not found")

    opt = OPTIMIZERS[req.run_id]
    state = RUN_STATES[req.run_id]

    try:
        severity = opt.disruption_engine.block_road(
            source=req.source,
            target=req.target,
            description=req.description or ""
        )
        opt.notify_disruption()

        # Update live state
        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        state["best_route"] = opt.best_evaluation.node_sequence if opt.best_evaluation else []
        state["detailed_path"] = opt.best_evaluation.detailed_path if opt.best_evaluation else []
        state["is_feasible"] = opt.best_evaluation.is_feasible if opt.best_evaluation else False

        return severity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/traffic-surge", response_model=DisruptionSeverity)
def traffic_surge_endpoint(req: TrafficSurgeRequest):
    if req.run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail="Optimizer run not found")

    opt = OPTIMIZERS[req.run_id]
    state = RUN_STATES[req.run_id]

    try:
        severity = opt.disruption_engine.inject_traffic_surge(
            edges=req.edges,
            factor=req.factor,
            description=req.description or ""
        )
        opt.notify_disruption()

        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/priority-change", response_model=DisruptionSeverity)
def priority_change_endpoint(req: PriorityChangeRequest):
    if req.run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail="Optimizer run not found")

    opt = OPTIMIZERS[req.run_id]
    state = RUN_STATES[req.run_id]

    try:
        severity = opt.disruption_engine.change_node_priority(
            node_id=req.node_id,
            new_priority=req.new_priority,
            description=req.description or ""
        )
        opt.notify_disruption()

        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vehicle-failure", response_model=DisruptionSeverity)
def vehicle_failure_endpoint(req: VehicleFailureRequest):
    if req.run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail="Optimizer run not found")

    opt = OPTIMIZERS[req.run_id]
    state = RUN_STATES[req.run_id]

    try:
        severity = opt.disruption_engine.simulate_vehicle_failure(
            capacity_loss_fraction=req.capacity_loss_fraction,
            description=req.description or ""
        )
        opt.notify_disruption()

        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
