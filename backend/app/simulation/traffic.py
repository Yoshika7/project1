"""
Traffic simulation and speed profile management for AdaptIQ-R.
Calculates dynamic congestion factors and travel times.
"""

from typing import List, Tuple
from backend.app.core.models import EdgeModel, NetworkScenarioModel


MAX_TRAFFIC_FACTOR = 5.0


def apply_traffic_surge(
    scenario: NetworkScenarioModel,
    edges_to_surge: List[Tuple[int, int]],
    factor: float = 2.5
) -> float:
    """
    Applies a traffic surge to specified edges.
    Returns the normalized traffic change relative to baseline.
    """
    surge_pairs = { (min(u, v), max(u, v)) for u, v in edges_to_surge }
    affected_count = 0

    for edge in scenario.edges:
        pair = (min(edge.source, edge.target), max(edge.source, edge.target))
        if pair in surge_pairs:
            edge.traffic_factor = min(MAX_TRAFFIC_FACTOR, max(1.0, factor))
            affected_count += 1

    return calculate_traffic_change_ratio(scenario)


def calculate_traffic_change_ratio(scenario: NetworkScenarioModel) -> float:
    """
    Calculates the normalized network-wide traffic increase in [0, 1].
    Baseline is 1.0 for all edges; maximum theoretical is MAX_TRAFFIC_FACTOR.
    """
    if not scenario.edges:
        return 0.0

    total_excess = sum(max(0.0, e.traffic_factor - 1.0) for e in scenario.edges)
    max_possible_excess = len(scenario.edges) * (MAX_TRAFFIC_FACTOR - 1.0)

    if max_possible_excess <= 0:
        return 0.0

    normalized = total_excess / max_possible_excess
    return min(1.0, max(0.0, normalized))
