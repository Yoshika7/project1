"""
Scenario generation API routes.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.models import NetworkScenarioModel
from backend.app.simulation.network_generator import generate_synthetic_network

router = APIRouter(prefix="/api/scenario", tags=["Scenario"])

# In-memory scenario storage
SCENARIOS: Dict[str, NetworkScenarioModel] = {}


class GenerateScenarioRequest(BaseModel):
    node_count: int = Field(default=20, description="10, 20, 50, or 100 nodes")
    seed: int = Field(default=42, description="Random seed for reproducible topology")
    grid_size: float = Field(default=100.0, description="Spatial bounding dimension")


@router.post("/generate", response_model=NetworkScenarioModel)
def generate_scenario(req: GenerateScenarioRequest):
    try:
        scenario = generate_synthetic_network(
            node_count=req.node_count,
            seed=req.seed,
            grid_size=req.grid_size
        )
        SCENARIOS[scenario.id] = scenario
        return scenario
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{scenario_id}", response_model=NetworkScenarioModel)
def get_scenario(scenario_id: str):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return SCENARIOS[scenario_id]
