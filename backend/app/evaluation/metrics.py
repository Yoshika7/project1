"""
Evaluation and telemetry metrics for AdaptIQ-R.
Computes real population diversity, fitness improvement, and recovery statistics.
"""

from typing import List, Set, Tuple
import math


def calculate_population_diversity(population: List[List[int]], sample_limit: int = 50) -> float:
    """
    Calculates population diversity based on normalized pairwise edge difference.
    Returns a value in [0.0, 1.0]:
    - 0.0: All individuals are identical.
    - 1.0: Maximum permutation divergence.
    """
    pop_size = len(population)
    if pop_size <= 1:
        return 0.0

    length = len(population[0])
    if length <= 2:
        return 0.0

    # Extract edge sets for each individual
    edge_sets: List[Set[Tuple[int, int]]] = []
    for ind in population[:sample_limit]:
        edges = set()
        for i in range(len(ind) - 1):
            u, v = ind[i], ind[i + 1]
            edges.add((min(u, v), max(u, v)))
        edge_sets.append(edges)

    num_sampled = len(edge_sets)
    total_diff = 0.0
    pair_count = 0
    max_possible_diff = float(length - 1)

    for i in range(num_sampled):
        for j in range(i + 1, num_sampled):
            # Symmetric difference between edge sets
            diff = len(edge_sets[i].symmetric_difference(edge_sets[j])) / 2.0
            total_diff += (diff / max_possible_diff)
            pair_count += 1

    if pair_count == 0:
        return 0.0

    avg_diversity = total_diff / float(pair_count)
    return round(min(1.0, max(0.0, avg_diversity)), 4)


def calculate_fitness_improvement(previous_best_fitness: float, current_best_fitness: float) -> float:
    """
    Calculates normalized fitness improvement from previous generation:
    improvement = (previous_best_fitness - current_best_fitness) / abs(previous_best_fitness)
    Clamped to [0.0, 1.0].
    """
    if previous_best_fitness == float("inf") or math.isinf(previous_best_fitness):
        return 0.0

    denom = abs(previous_best_fitness)
    if denom < 1e-9:
        return 0.0

    raw_improvement = (previous_best_fitness - current_best_fitness) / denom
    clamped = max(0.0, min(1.0, raw_improvement))
    return round(clamped, 4)
