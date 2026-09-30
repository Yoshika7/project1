"""
Tests for Genetic Algorithm Operators and Execution.
"""

import random
import pytest
from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.optimizer.population import initialize_population
from backend.app.optimizer.selection import tournament_selection
from backend.app.optimizer.crossover import order_crossover
from backend.app.optimizer.mutation import swap_mutation
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.core.models import OptimizationConfig


def test_population_initialization():
    customers = list(range(1, 15))
    pop = initialize_population(customers, population_size=50)

    assert len(pop) == 50
    for ind in pop:
        assert sorted(ind) == customers
        assert len(ind) == len(customers)


def test_order_crossover():
    p1 = [1, 2, 3, 4, 5, 6, 7, 8]
    p2 = [8, 7, 6, 5, 4, 3, 2, 1]

    rng = random.Random(42)
    c1, c2 = order_crossover(p1, p2, rng=rng)

    assert sorted(c1) == sorted(p1)
    assert sorted(c2) == sorted(p2)
    assert len(c1) == len(p1)
    assert len(c2) == len(p2)


def test_swap_mutation():
    chrom = [1, 2, 3, 4, 5, 6, 7, 8]
    rng = random.Random(42)

    # 100% mutation rate guarantees modification
    mutated = swap_mutation(chrom, mutation_rate=1.0, exploration_level=0.5, rng=rng)
    assert sorted(mutated) == sorted(chrom)
    assert mutated != chrom

    # 0% mutation rate keeps identical
    mutated_none = swap_mutation(chrom, mutation_rate=0.0, exploration_level=0.5, rng=rng)
    assert mutated_none == chrom


def test_tournament_selection():
    pop = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    fitnesses = [10.0, 5.0, 1.0]  # index 2 is best
    rng = random.Random(42)

    winner = tournament_selection(pop, fitnesses, tournament_size=3, exploration_level=0.1, rng=rng)
    assert winner == [7, 8, 9]


def test_elitism_preservation():
    scenario = generate_synthetic_network(node_count=10, seed=42)
    cfg = OptimizationConfig(population_size=40, generations=10, elite_ratio=0.1, is_adaptive=False)
    opt = GeneticAlgorithmOptimizer(scenario, cfg)

    m1 = opt.step()
    best_f1 = m1.best_fitness
    m2 = opt.step()
    best_f2 = m2.best_fitness

    # Elitism ensures best fitness never degrades during normal static conditions
    assert best_f2 <= best_f1 + 1e-6
