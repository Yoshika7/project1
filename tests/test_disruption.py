"""
Tests for Disruption Engine, Severity Calculation, and Adaptive Rerouting.
"""

import pytest
from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.core.models import OptimizationConfig


def test_disruption_types_and_severity():
    scenario = generate_synthetic_network(node_count=20, seed=42)
    engine = DisruptionEngine(scenario)

    # 1. Road block
    edge = scenario.edges[0]
    sev1 = engine.block_road(edge.source, edge.target)
    assert sev1.severity > 0.0
    assert sev1.blocked_edge_ratio > 0.0
    assert edge.blocked is True

    # 2. Traffic surge
    e2 = scenario.edges[1]
    sev2 = engine.inject_traffic_surge([(e2.source, e2.target)], factor=3.0)
    assert sev2.normalized_traffic_change > 0.0
    assert sev2.severity > sev1.severity

    # 3. Priority change
    sev3 = engine.change_node_priority(node_id=2, new_priority=3)
    assert sev3.normalized_priority_change > 0.0
    assert sev3.severity > sev2.severity

    # 4. Vehicle failure
    sev4 = engine.simulate_vehicle_failure(capacity_loss_fraction=0.5)
    assert sev4.vehicle_change == 0.5
    assert sev4.severity > sev3.severity
    assert 0.0 <= sev4.severity <= 1.0


def test_successful_rerouting_around_blocked_edge():
    """
    CRITICAL REQUIREMENT:
    When a road used by the current route is blocked,
    the optimizer can produce a different feasible route avoiding the blocked edge.
    """
    scenario = generate_synthetic_network(node_count=10, seed=42)
    cfg = OptimizationConfig(
        population_size=60,
        generations=30,
        is_adaptive=True,
        seed=42
    )
    disrupt_engine = DisruptionEngine(scenario)
    opt = GeneticAlgorithmOptimizer(scenario, cfg, disruption_engine=disrupt_engine)

    # Initial optimization
    opt.run(30)
    initial_route = list(opt.best_evaluation.node_sequence)
    initial_traversed = list(opt.best_evaluation.traversed_edges)
    assert len(initial_traversed) > 0

    # Block one edge actively used in initial route
    block_u, block_v = initial_traversed[0]
    disrupt_engine.block_road(block_u, block_v)
    opt.notify_disruption()

    # Recovery optimization
    opt.run(40)
    recovered_eval = opt.best_evaluation
    recovered_pair = (min(block_u, block_v), max(block_u, block_v))

    assert recovered_eval.is_feasible is True
    # Recovered route must NOT traverse the blocked edge
    assert recovered_pair not in recovered_eval.traversed_edges
