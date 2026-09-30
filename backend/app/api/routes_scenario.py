"""
Scenario generation API routes for AdaptIQ-R.

Handles creation and retrieval of synthetic road-network scenarios used as the
environment for the Adaptive Genetic Algorithm route optimizer.

Supports UN SDG 11 (Sustainable Cities) by modelling realistic urban delivery
networks with configurable node counts, spatial scale, and reproducible seeds.

Routes
------
POST /api/scenario/generate  — Create a new synthetic network scenario.
GET  /api/scenario/{id}      — Retrieve an existing scenario by ID.
"""

from __future__ import annotations

import functools
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.models import NetworkScenarioModel
from backend.app.simulation.network_generator import generate_synthetic_network

router = APIRouter(prefix="/api/scenario", tags=["Scenario"])

# ---------------------------------------------------------------------------
# In-memory scenario registry (scenario_id → NetworkScenarioModel)
# ---------------------------------------------------------------------------
SCENARIOS: Dict[str, NetworkScenarioModel] = {}


# ---------------------------------------------------------------------------
# Response/request schemas
# ---------------------------------------------------------------------------


class GenerateScenarioRequest(BaseModel):
    """Request body for synthetic road-network generation.

    Attributes
    ----------
    node_count:
        Total number of nodes (depot + delivery stops). Supported sizes: 10, 20,
        50, 100. Larger values increase computational cost of Dijkstra routing.
    seed:
        Integer random seed.  Identical seeds produce identical node positions,
        edges, and demand assignments — required for scientific reproducibility.
    grid_size:
        Euclidean bounding-box side length (arbitrary units). Scales all
        inter-node distances proportionally.
    """

    node_count: int = Field(
        default=20,
        ge=5,
        le=200,
        description="Number of nodes (depot + customers). Supported: 10, 20, 50, 100.",
    )
    seed: int = Field(
        default=42,
        description="RNG seed for fully reproducible topology and demand.",
    )
    grid_size: float = Field(
        default=100.0,
        gt=0.0,
        description="Spatial bounding dimension (arbitrary distance units).",
    )


# ---------------------------------------------------------------------------
# Cached network generator — memoises (node_count, seed, grid_size) triples
# so repeated identical requests do not rerun MST/kNN construction.
# Cache miss: O(N² log N); Cache hit: O(1).
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=64)
def _cached_generate(node_count: int, seed: int, grid_size: float) -> NetworkScenarioModel:
    """Return a memoised synthetic network for the given parameter triple.

    Wraps :func:`generate_synthetic_network` with an LRU cache keyed on
    ``(node_count, seed, grid_size)``.  The cache holds up to 64 distinct
    parameter combinations; eviction follows LRU policy.

    Parameters
    ----------
    node_count:
        Number of nodes (depot + delivery customers).
    seed:
        Deterministic RNG seed.
    grid_size:
        Euclidean bounding-box dimension.

    Returns
    -------
    NetworkScenarioModel
        Fully constructed scenario with nodes, edges, and demand assignments.

    Complexity
    ----------
    Cache miss : O(N² log N) — MST + kNN graph construction.
    Cache hit  : O(1) — direct dictionary lookup.
    """
    return generate_synthetic_network(
        node_count=node_count,
        seed=seed,
        grid_size=grid_size,
    )


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=NetworkScenarioModel, summary="Generate synthetic road network")
async def generate_scenario(req: GenerateScenarioRequest) -> NetworkScenarioModel:
    """Generate a new synthetic urban road-network scenario.

    Creates a planar-like graph using Kruskal's MST for baseline connectivity
    and k-nearest neighbours for additional realism.  Each scenario is stored
    in the in-memory registry and can be retrieved by its auto-generated ID.

    Parameters
    ----------
    req:
        Generation parameters (node count, seed, grid size).

    Returns
    -------
    NetworkScenarioModel
        The generated scenario including all nodes, edges, demands, and
        the unique scenario ID for subsequent API calls.

    Raises
    ------
    HTTPException (400)
        If the requested parameters produce an invalid network.
    """
    try:
        # O(1) on cache hit; O(N² log N) on miss — LRU cache avoids redundant work
        scenario = _cached_generate(
            node_count=req.node_count,
            seed=req.seed,
            grid_size=req.grid_size,
        )
        # Store under its unique ID for retrieval by disruption/optimization routes
        SCENARIOS[scenario.id] = scenario
        return scenario
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/{scenario_id}",
    response_model=NetworkScenarioModel,
    summary="Retrieve an existing scenario",
)
async def get_scenario(scenario_id: str) -> NetworkScenarioModel:
    """Retrieve a previously generated scenario by its unique ID.

    Parameters
    ----------
    scenario_id:
        The UUID-style identifier returned by ``POST /api/scenario/generate``.

    Returns
    -------
    NetworkScenarioModel
        The stored scenario object.

    Raises
    ------
    HTTPException (404)
        If no scenario with the given ID exists in the registry.
    """
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return SCENARIOS[scenario_id]
