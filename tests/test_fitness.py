"""
Tests for AdaptIQ-R Fitness Engine and Shortest Path Evaluation.
"""

import pytest
from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.optimizer.fitness import FitnessEngine
from backend.app.simulation.disruption_engine import DisruptionEngine


def test_fitness_distance_and_travel_time():
    scenario = generate_synthetic_network(node_count=10, seed=42)
    engine = FitnessEngine(scenario)

    candidate = list(range(1, 10))
    eval_res = engine.evaluate_route(candidate)

    assert eval_res.total_distance > 0.0
    assert eval_res.total_travel_time > 0.0
    assert eval_res.fitness > 0.0
    assert eval_res.is_feasible is True
    assert eval_res.node_sequence[0] == 0
    assert eval_res.node_sequence[-1] == 0
    assert len(eval_res.detailed_path) >= len(eval_res.node_sequence)


def test_blocked_road_handling():
    scenario = generate_synthetic_network(node_count=10, seed=42)
    engine = FitnessEngine(scenario)

    candidate = list(range(1, 10))
    initial_eval = engine.evaluate_route(candidate)

    # Block an edge that was traversed
    assert len(initial_eval.traversed_edges) > 0
    u, v = initial_eval.traversed_edges[0]

    disrupt = DisruptionEngine(scenario)
    disrupt.block_road(u, v)
    engine.invalidate_cache()

    rerouted_eval = engine.evaluate_route(candidate)
    pair = (min(u, v), max(u, v))
    assert pair not in rerouted_eval.traversed_edges


def test_unreachable_route_handling():
    scenario = generate_synthetic_network(node_count=10, seed=42)
    # Block all edges connected to node 1
    for edge in scenario.edges:
        if edge.source == 1 or edge.target == 1:
            edge.blocked = True

    engine = FitnessEngine(scenario)
    candidate = list(range(1, 10))
    eval_res = engine.evaluate_route(candidate)

    assert eval_res.is_feasible is False
    assert len(eval_res.unreachable_segments) > 0
    assert eval_res.constraint_penalty >= 1000.0


def test_penalty_calculation():
    scenario = generate_synthetic_network(node_count=10, seed=42)
    # Set node 9 as high priority
    scenario.nodes[9].priority = 3
    scenario.nodes[9].type = "priority"

    engine = FitnessEngine(scenario)
    # Put priority node at the very end
    late_seq = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    eval_late = engine.evaluate_route(late_seq)

    # Put priority node early
    early_seq = [9, 1, 2, 3, 4, 5, 6, 7, 8]
    eval_early = engine.evaluate_route(early_seq)

    assert eval_late.constraint_penalty >= eval_early.constraint_penalty
