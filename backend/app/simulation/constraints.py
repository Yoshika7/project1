"""
Route constraints and penalty evaluation for AdaptIQ-R.
Validates priority sequencing, capacity thresholds, and road viability.
"""

from typing import List, Dict
from backend.app.core.models import NodeModel
from backend.app.core.config import (
    PENALTY_PRIORITY_VIOLATION,
    PENALTY_CAPACITY_VIOLATION,
)


def evaluate_priority_penalty(
    node_sequence: List[int],
    nodes: Dict[int, NodeModel]
) -> float:
    """
    Evaluates penalty for serving high-priority stops late in the route.
    Penalizes based on the fraction of the route that elapsed before serving priority nodes.
    """
    penalty = 0.0
    total_stops = len(node_sequence)
    if total_stops <= 1:
        return 0.0

    for idx, node_id in enumerate(node_sequence):
        node = nodes.get(node_id)
        if node and node.type == "priority":
            # Normalized position from 0.0 (start) to 1.0 (end)
            pos_ratio = idx / float(total_stops - 1)
            # If served in the second half of the route, penalize proportional to delay
            if pos_ratio > 0.4:
                penalty += PENALTY_PRIORITY_VIOLATION * (pos_ratio - 0.4) * node.priority

    return round(penalty, 2)


def evaluate_capacity_penalty(
    node_sequence: List[int],
    nodes: Dict[int, NodeModel],
    vehicle_capacity: float = 30.0
) -> float:
    """
    Evaluates penalty if cumulative demand exceeds vehicle capacity.
    """
    total_demand = sum(nodes[nid].demand for nid in node_sequence if nid in nodes)
    if total_demand > vehicle_capacity:
        excess = total_demand - vehicle_capacity
        return round(PENALTY_CAPACITY_VIOLATION * (excess / vehicle_capacity), 2)
    return 0.0
