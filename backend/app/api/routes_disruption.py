"""
Disruption injection API routes for AdaptIQ-R.

Exposes four disruption types that can be applied to an active optimization run
mid-execution.  Each endpoint modifies the road-network graph state and triggers
a fitness cache invalidation + population re-evaluation inside the optimizer.

Disruption types align with UN SDG 11 resilience research:
- Road Block  : Simulates infrastructure failure (blocked bridge, accident)
- Traffic Surge : Simulates congestion events
- Priority Change : Simulates urgent delivery re-prioritisation
- Vehicle Failure : Simulates fleet capacity reduction

All endpoints are async so they do not block the FastAPI event loop while
the synchronous re-evaluation runs inside the calling thread context.

Routes
------
POST /api/disruption/road-block       — Block a road segment.
POST /api/disruption/traffic-surge    — Apply traffic congestion multiplier.
POST /api/disruption/priority-change  — Elevate a customer delivery priority.
POST /api/disruption/vehicle-failure  — Reduce fleet capacity.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.models import DisruptionSeverity
from backend.app.api.routes_optimization import OPTIMIZERS, RUN_STATES
from backend.app.api.routes_scenario import SCENARIOS

router = APIRouter(prefix="/api/disruption", tags=["Disruption"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RoadBlockRequest(BaseModel):
    """Request body for blocking a road segment.

    Attributes
    ----------
    run_id:
        Active optimization run to apply the disruption to.
    source:
        Source node ID of the edge to block.
    target:
        Target node ID of the edge to block.
    description:
        Optional human-readable label for this disruption event.
    """

    run_id: str
    source: int
    target: int
    description: Optional[str] = None


class TrafficSurgeRequest(BaseModel):
    """Request body for applying a traffic congestion multiplier.

    Attributes
    ----------
    run_id:
        Active optimization run to apply the disruption to.
    edges:
        List of (source, target) edge pairs to affect.
    factor:
        Traffic congestion multiplier in [1.0, 5.0].  A value of 2.5 means
        travel time on affected edges is 2.5× the base value.
    description:
        Optional human-readable label.
    """

    run_id: str
    edges: List[Tuple[int, int]]
    factor: float = Field(default=2.5, ge=1.0, le=5.0)
    description: Optional[str] = None


class PriorityChangeRequest(BaseModel):
    """Request body for changing a customer node's delivery priority.

    Attributes
    ----------
    run_id:
        Active optimization run to apply the disruption to.
    node_id:
        ID of the customer node whose priority is being changed.
    new_priority:
        Integer priority level in [1, 5].  Higher values impose stronger
        penalty if the node is visited late in the route sequence.
    description:
        Optional human-readable label.
    """

    run_id: str
    node_id: int
    new_priority: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None


class VehicleFailureRequest(BaseModel):
    """Request body for simulating a vehicle breakdown.

    Attributes
    ----------
    run_id:
        Active optimization run to apply the disruption to.
    capacity_loss_fraction:
        Fraction of fleet capacity lost in [0.1, 1.0].
        0.5 means 50% capacity reduction.
    description:
        Optional human-readable label.
    """

    run_id: str
    capacity_loss_fraction: float = Field(default=0.5, ge=0.1, le=1.0)
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_optimizer_or_404(run_id: str):
    """Retrieve optimizer and state dict, raising 404 if not found.

    Parameters
    ----------
    run_id:
        Optimization run identifier.

    Returns
    -------
    tuple
        ``(optimizer, state_dict)``

    Raises
    ------
    HTTPException (404)
        If ``run_id`` is not registered in ``OPTIMIZERS``.
    """
    if run_id not in OPTIMIZERS:
        raise HTTPException(status_code=404, detail=f"Optimizer run '{run_id}' not found.")
    return OPTIMIZERS[run_id], RUN_STATES[run_id]


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.post(
    "/road-block",
    response_model=DisruptionSeverity,
    summary="Block a road segment mid-optimization",
)
async def block_road_endpoint(req: RoadBlockRequest) -> DisruptionSeverity:
    """Apply a road-block disruption to an active optimization run.

    Blocks the edge between ``source`` and ``target`` in both directions,
    invalidates the fitness engine's path cache, and triggers a full
    population re-evaluation under the new network topology.

    Parameters
    ----------
    req:
        Road-block request specifying the run and edge to block.

    Returns
    -------
    DisruptionSeverity
        Composite severity score reflecting all currently active disruptions.

    Raises
    ------
    HTTPException (400)
        If the edge does not exist or another validation error occurs.
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    opt, state = _get_optimizer_or_404(req.run_id)
    try:
        severity: DisruptionSeverity = opt.disruption_engine.block_road(
            source=req.source,
            target=req.target,
            description=req.description or "",
        )
        # Invalidate cache + re-evaluate population under the new graph state
        opt.notify_disruption()

        # Update live telemetry state for polling endpoints
        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        state["best_route"] = (
            opt.best_evaluation.node_sequence if opt.best_evaluation else []
        )
        state["detailed_path"] = (
            opt.best_evaluation.detailed_path if opt.best_evaluation else []
        )
        state["is_feasible"] = (
            opt.best_evaluation.is_feasible if opt.best_evaluation else False
        )
        return severity
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/traffic-surge",
    response_model=DisruptionSeverity,
    summary="Apply traffic congestion to road edges",
)
async def traffic_surge_endpoint(req: TrafficSurgeRequest) -> DisruptionSeverity:
    """Apply a traffic-surge congestion multiplier to specified edges.

    Multiplies the travel time of each specified edge by ``factor``, triggering
    re-evaluation of the current population under the new congestion state.

    Parameters
    ----------
    req:
        Traffic-surge request with edge list and congestion factor.

    Returns
    -------
    DisruptionSeverity
        Updated composite severity score.

    Raises
    ------
    HTTPException (400)
        If the request parameters are invalid.
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    opt, state = _get_optimizer_or_404(req.run_id)
    try:
        severity: DisruptionSeverity = opt.disruption_engine.inject_traffic_surge(
            edges=req.edges,
            factor=req.factor,
            description=req.description or "",
        )
        opt.notify_disruption()
        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/priority-change",
    response_model=DisruptionSeverity,
    summary="Elevate a customer delivery priority",
)
async def priority_change_endpoint(req: PriorityChangeRequest) -> DisruptionSeverity:
    """Change the delivery priority of a customer node mid-optimization.

    Higher priority values increase the penalty applied when this node is
    visited late in the route sequence, steering the GA toward front-loading
    high-priority deliveries.

    Parameters
    ----------
    req:
        Priority-change request with node ID and new priority level.

    Returns
    -------
    DisruptionSeverity
        Updated composite severity score.

    Raises
    ------
    HTTPException (400)
        If the node ID is invalid.
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    opt, state = _get_optimizer_or_404(req.run_id)
    try:
        severity: DisruptionSeverity = opt.disruption_engine.change_node_priority(
            node_id=req.node_id,
            new_priority=req.new_priority,
            description=req.description or "",
        )
        opt.notify_disruption()
        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/vehicle-failure",
    response_model=DisruptionSeverity,
    summary="Simulate fleet vehicle breakdown",
)
async def vehicle_failure_endpoint(req: VehicleFailureRequest) -> DisruptionSeverity:
    """Simulate a vehicle breakdown reducing total fleet delivery capacity.

    Reduces the available capacity ratio and updates the capacity-violation
    penalty used during fitness evaluation.

    Parameters
    ----------
    req:
        Vehicle-failure request with capacity loss fraction.

    Returns
    -------
    DisruptionSeverity
        Updated composite severity score.

    Raises
    ------
    HTTPException (400)
        If the capacity loss fraction is out of range.
    HTTPException (404)
        If the ``run_id`` is not registered.
    """
    opt, state = _get_optimizer_or_404(req.run_id)
    try:
        severity: DisruptionSeverity = opt.disruption_engine.simulate_vehicle_failure(
            capacity_loss_fraction=req.capacity_loss_fraction,
            description=req.description or "",
        )
        opt.notify_disruption()
        state["disruption_severity"] = severity.severity
        state["best_fitness"] = opt.best_fitness
        return severity
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
