"""
Data models for AdaptIQ-R.
Strongly typed Pydantic models and dataclasses for network scenarios,
routes, disruptions, fuzzy logic, and optimization telemetry.
"""

from typing import List, Dict, Tuple, Optional, Any, Literal
from pydantic import BaseModel, Field


NodeType = Literal["depot", "customer", "priority"]
DisruptionType = Literal["road_block", "traffic_surge", "priority_change", "vehicle_failure"]


class NodeModel(BaseModel):
    id: int
    x: float
    y: float
    type: NodeType = "customer"
    priority: int = 1
    demand: float = 1.0


class EdgeModel(BaseModel):
    source: int
    target: int
    distance: float
    travel_time: float
    traffic_factor: float = 1.0
    blocked: bool = False


class NetworkScenarioModel(BaseModel):
    id: str
    seed: int
    node_count: int
    depot_id: int = 0
    nodes: Dict[int, NodeModel]
    edges: List[EdgeModel]


class RouteEvaluation(BaseModel):
    node_sequence: List[int]
    detailed_path: List[int] = Field(default_factory=list)
    total_distance: float
    total_travel_time: float
    constraint_penalty: float
    fitness: float
    is_feasible: bool = True
    traversed_edges: List[Tuple[int, int]] = Field(default_factory=list)
    unreachable_segments: List[Tuple[int, int]] = Field(default_factory=list)


class DisruptionSeverity(BaseModel):
    severity: float = Field(ge=0.0, le=1.0)
    blocked_edge_ratio: float = 0.0
    normalized_traffic_change: float = 0.0
    normalized_priority_change: float = 0.0
    vehicle_change: float = 0.0


class DisruptionEvent(BaseModel):
    disruption_type: DisruptionType
    target_id: Optional[str] = None
    value: Any = None
    timestamp: float = 0.0
    description: str = ""


class FuzzyDiagnostic(BaseModel):
    diversity: float
    fitness_improvement: float
    disruption_severity: float
    mutation_rate: float
    exploration_level: float
    activated_rules: List[str] = Field(default_factory=list)


class GenerationMetric(BaseModel):
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    population_diversity: float
    fitness_improvement: float
    disruption_severity: float
    mutation_rate: float
    exploration_level: float
    activated_rules: List[str] = Field(default_factory=list)
    best_route: List[int]
    detailed_path: List[int] = Field(default_factory=list)
    is_feasible: bool = True
    total_distance: float
    total_travel_time: float
    constraint_penalty: float = 0.0


class OptimizationConfig(BaseModel):
    seed: int = 42
    population_size: int = 100
    generations: int = 200
    elite_ratio: float = 0.05
    crossover_rate: float = 0.85
    initial_mutation_rate: float = 0.15
    distance_weight: float = 0.45
    time_weight: float = 0.35
    penalty_weight: float = 0.20
    tournament_size: int = 3
    convergence_threshold: float = 1e-4
    stagnation_limit: int = 50
    is_adaptive: bool = True  # True for AdaptIQ-R, False for Baseline GA


class OptimizationState(BaseModel):
    run_id: str
    status: Literal["idle", "running", "paused", "completed", "failed"] = "idle"
    scenario_id: str = ""
    current_generation: int = 0
    total_generations: int = 0
    best_fitness: float = float("inf")
    best_route: List[int] = Field(default_factory=list)
    detailed_path: List[int] = Field(default_factory=list)
    diversity: float = 0.0
    mutation_rate: float = 0.15
    exploration_level: float = 0.5
    disruption_severity: float = 0.0
    activated_rules: List[str] = Field(default_factory=list)
    history: List[GenerationMetric] = Field(default_factory=list)
    disruptions_applied: List[DisruptionEvent] = Field(default_factory=list)
    error_message: Optional[str] = None
