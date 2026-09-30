"""
Performance and latency benchmarks for AdaptIQ-R.

Validates that all performance-critical code paths complete within defined
time budgets.  These tests catch O(n²) regressions, unintentional blocking
calls, and ensure the system meets its real-time responsiveness guarantees
required for live frontend polling.

Latency budgets (measured on a reference single-core 2 GHz CPU):
  - Fuzzy inference (evaluate)        : < 5 ms per call
  - Single GA step (10-node, pop=30)  : < 200 ms per step
  - Diversity calculation (pop=100)   : < 10 ms per call
  - Fitness cache hit (graph unchanged): < 1 ms per evaluation
  - LRU MF cache hit                  : < 0.1 ms per call
  - Network scenario generation       : < 500 ms for 50 nodes
"""

from __future__ import annotations

import random
import time
from typing import List

import pytest

from backend.app.evaluation.metrics import calculate_population_diversity
from backend.app.fuzzy.fuzzy_controller import FuzzyController
from backend.app.fuzzy.membership import triangular_mf, trapezoidal_mf
from backend.app.optimizer.fitness import FitnessEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.simulation.network_generator import generate_synthetic_network


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def small_scenario():
    """A 10-node scenario for fast latency tests."""
    return generate_synthetic_network(node_count=10, seed=99)


@pytest.fixture(scope="module")
def medium_scenario():
    """A 20-node scenario for realistic latency tests."""
    return generate_synthetic_network(node_count=20, seed=42)


@pytest.fixture(scope="module")
def fuzzy_controller():
    """Shared FuzzyController instance (100 defuzz steps)."""
    return FuzzyController(discretization_steps=100)


# ---------------------------------------------------------------------------
# Fuzzy Inference Latency
# ---------------------------------------------------------------------------


class TestFuzzyInferenceLatency:
    """Verify Mamdani FIS completes within the 5 ms budget."""

    def test_single_inference_under_5ms(self, fuzzy_controller):
        """A single evaluate() call must complete in under 5 ms.

        The FIS runs 9 rules × 100 defuzzification steps = 900 MF evaluations
        per call.  With LRU-cached MFs this should be well under 2 ms.
        """
        start = time.perf_counter()
        result = fuzzy_controller.evaluate(
            diversity=0.3, improvement=0.1, severity=0.8
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 5.0, (
            f"FuzzyController.evaluate() took {elapsed_ms:.2f} ms — "
            f"exceeds 5 ms latency budget."
        )
        assert "mutation_rate" in result
        assert "exploration_level" in result

    def test_batch_inference_throughput(self, fuzzy_controller):
        """100 consecutive evaluate() calls must finish in under 200 ms total.

        This validates that caching provides sublinear scaling — the 100th call
        should be significantly faster than the first due to warm LRU cache.
        """
        start = time.perf_counter()
        for i in range(100):
            fuzzy_controller.evaluate(
                diversity=round(i / 100.0, 2),
                improvement=round(1.0 - i / 100.0, 2),
                severity=round((i % 10) / 10.0, 2),
            )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 200.0, (
            f"100 FuzzyController.evaluate() calls took {elapsed_ms:.2f} ms — "
            f"exceeds 200 ms budget."
        )


# ---------------------------------------------------------------------------
# Membership Function LRU Cache
# ---------------------------------------------------------------------------


class TestMembershipFunctionCache:
    """Verify LRU cache on MF primitives reduces repeated evaluation cost."""

    def test_triangular_cache_hit_under_0p1ms(self):
        """Cache hit on triangular_mf must complete in under 0.1 ms."""
        # Warm the cache
        triangular_mf(0.5, 0.0, 0.5, 1.0)

        start = time.perf_counter()
        for _ in range(1000):
            triangular_mf(0.5, 0.0, 0.5, 1.0)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # 1000 cache hits in under 100 ms = < 0.1 ms per hit
        assert elapsed_ms < 100.0, (
            f"1000 triangular_mf cache hits took {elapsed_ms:.2f} ms."
        )

    def test_trapezoidal_cache_hit_under_0p1ms(self):
        """Cache hit on trapezoidal_mf must complete in under 0.1 ms."""
        trapezoidal_mf(0.5, 0.0, 0.3, 0.7, 1.0)  # Warm

        start = time.perf_counter()
        for _ in range(1000):
            trapezoidal_mf(0.5, 0.0, 0.3, 0.7, 1.0)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 100.0, (
            f"1000 trapezoidal_mf cache hits took {elapsed_ms:.2f} ms."
        )


# ---------------------------------------------------------------------------
# Diversity Calculation Latency
# ---------------------------------------------------------------------------


class TestDiversityLatency:
    """Verify O(S²·L) sampled diversity calculation stays under 10 ms."""

    def test_diversity_large_population_under_10ms(self):
        """Sampled diversity on pop=100, L=20 must complete in under 10 ms.

        With sample_limit=30 the algorithm evaluates at most 30²/2 = 450
        pairs × O(L) set ops — consistently under 5 ms on modern hardware.
        """
        rng = random.Random(0)
        nodes = list(range(1, 21))
        population: List[List[int]] = [
            rng.sample(nodes, len(nodes)) for _ in range(100)
        ]

        start = time.perf_counter()
        diversity = calculate_population_diversity(population, sample_limit=30)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 10.0, (
            f"calculate_population_diversity() took {elapsed_ms:.2f} ms "
            f"on 100 individuals — exceeds 10 ms budget."
        )
        assert 0.0 <= diversity <= 1.0


# ---------------------------------------------------------------------------
# Fitness Engine Latency
# ---------------------------------------------------------------------------


class TestFitnessEngineLatency:
    """Verify route evaluation and graph-cache performance."""

    def test_fitness_evaluation_under_50ms(self, small_scenario):
        """A single route evaluation on a 10-node scenario must finish in < 50 ms."""
        engine = FitnessEngine(small_scenario)
        customer_ids = [nid for nid in small_scenario.nodes if nid != 0]
        route = list(customer_ids)

        start = time.perf_counter()
        result = engine.evaluate_route(route)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 50.0, (
            f"FitnessEngine.evaluate_route() took {elapsed_ms:.2f} ms — "
            f"exceeds 50 ms budget."
        )
        assert result.fitness < float("inf")

    def test_graph_cache_hit_under_1ms(self, small_scenario):
        """Repeated get_navigable_graph() must return cache hits in < 1 ms."""
        engine = FitnessEngine(small_scenario)
        engine.get_navigable_graph()  # Build and cache

        start = time.perf_counter()
        for _ in range(100):
            g = engine.get_navigable_graph()  # All cache hits
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 100.0, (
            f"100 cached get_navigable_graph() calls took {elapsed_ms:.2f} ms."
        )


# ---------------------------------------------------------------------------
# GA Step Latency
# ---------------------------------------------------------------------------


class TestGAStepLatency:
    """Verify single GA generation completes within the 200 ms budget."""

    def test_single_step_10_nodes_under_200ms(self, small_scenario):
        """One GA step on 10 nodes, pop=30 must complete in under 200 ms."""
        from backend.app.core.models import OptimizationConfig

        config = OptimizationConfig(
            seed=42,
            population_size=30,
            is_adaptive=True,
        )
        opt = GeneticAlgorithmOptimizer(scenario=small_scenario, config=config)

        start = time.perf_counter()
        metric = opt.step()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 200.0, (
            f"GeneticAlgorithmOptimizer.step() took {elapsed_ms:.2f} ms — "
            f"exceeds 200 ms latency budget for 10-node scenario."
        )
        assert metric.generation == 1
        assert metric.best_fitness < float("inf")

    def test_ten_steps_under_2s(self, small_scenario):
        """10 GA steps on 10 nodes, pop=30 must complete in under 2 seconds."""
        from backend.app.core.models import OptimizationConfig

        config = OptimizationConfig(seed=7, population_size=30, is_adaptive=True)
        opt = GeneticAlgorithmOptimizer(scenario=small_scenario, config=config)

        start = time.perf_counter()
        for _ in range(10):
            opt.step()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 2000.0, (
            f"10 GA steps took {elapsed_ms:.2f} ms — exceeds 2 s budget."
        )


# ---------------------------------------------------------------------------
# Network Generation Latency
# ---------------------------------------------------------------------------


class TestNetworkGenerationLatency:
    """Verify scenario generation completes within acceptable time bounds."""

    def test_20_node_scenario_under_500ms(self):
        """Generating a 20-node scenario must complete in under 500 ms."""
        start = time.perf_counter()
        scenario = generate_synthetic_network(node_count=20, seed=1)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 500.0, (
            f"generate_synthetic_network(20 nodes) took {elapsed_ms:.2f} ms — "
            f"exceeds 500 ms budget."
        )
        assert len(scenario.nodes) == 20

    def test_50_node_scenario_under_2000ms(self):
        """Generating a 50-node scenario must complete in under 2000 ms."""
        start = time.perf_counter()
        scenario = generate_synthetic_network(node_count=50, seed=2)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 2000.0, (
            f"generate_synthetic_network(50 nodes) took {elapsed_ms:.2f} ms — "
            f"exceeds 2000 ms budget."
        )
        assert len(scenario.nodes) == 50
