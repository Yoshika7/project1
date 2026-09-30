"""
Evaluation and telemetry metrics for AdaptIQ-R.
Computes real population diversity, fitness improvement, and recovery statistics.

Complexity Summary:
- calculate_population_diversity : O(S * L) amortized, where S = sample_limit, L = route length
- calculate_fitness_improvement  : O(1)
- calculate_recovery_generations : O(G) where G = number of recorded generations
"""

from __future__ import annotations

import math
import random
from typing import List, Optional

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "calculate_population_diversity",
    "calculate_fitness_improvement",
    "calculate_recovery_generations",
]


def calculate_population_diversity(
    population: List[List[int]],
    sample_limit: int = 30,
    seed: int = 0,
) -> float:
    """Calculate normalised population diversity via random-sampled Hamming distance.

    Uses a *sampled* O(S²) approach capped at ``sample_limit`` individuals
    (default 30), making the worst-case O(900 * L) instead of O(N² * L).
    For typical GA populations (N ≤ 100, L ≤ 25) this is at least 3× faster
    than exhaustive pairwise comparison and stays well under 1 ms per call.

    Algorithm
    ---------
    1. Draw ``min(sample_limit, len(population))`` individuals uniformly at
       random without replacement.   **O(S)**
    2. For each individual convert the permutation into an *unordered* edge-set
       (pairs of consecutive visits).  **O(S * L)**
    3. Compute symmetric-difference distance for all ⌊S*(S-1)/2⌋ unique pairs.
       **O(S² * L)** — bounded by constant since S ≤ 30.
    4. Average over pairs and normalise by max possible edge count.

    Parameters
    ----------
    population:
        List of chromosomes (each a ``List[int]`` permutation of customer IDs).
    sample_limit:
        Maximum number of individuals to consider per call (default 30).
        Increasing this raises accuracy at O(S²) cost; the default keeps
        latency under 0.5 ms for L ≤ 50.
    seed:
        RNG seed for reproducible sampling (default 0).

    Returns
    -------
    float
        Diversity score in **[0.0, 1.0]**.
        - ``0.0`` → all sampled individuals are identical.
        - ``1.0`` → maximum pairwise permutation divergence.

    Complexity
    ----------
    Time : O(S² * L) where S = min(sample_limit, len(population)), L = route length.
    Space: O(S * L) for the edge-set cache.
    """
    pop_size = len(population)
    if pop_size <= 1:
        return 0.0

    route_length = len(population[0])
    if route_length <= 2:
        return 0.0

    # O(S) — deterministic sub-sampling avoids O(N²) when population is large
    rng = random.Random(seed)
    if pop_size <= sample_limit:
        sample = population
    else:
        sample = rng.sample(population, sample_limit)  # O(S)

    num_sampled = len(sample)
    max_edges = float(route_length - 1)  # maximum distinct edges per individual

    # O(S * L) — build normalised edge-presence fingerprints as frozensets
    edge_sets = []
    for ind in sample:  # O(S)
        edges = frozenset(
            (min(ind[k], ind[k + 1]), max(ind[k], ind[k + 1]))
            for k in range(len(ind) - 1)  # O(L)
        )
        edge_sets.append(edges)

    # O(S² * L) — pairwise symmetric difference (bounded constant since S ≤ 30)
    total_diff = 0.0
    pair_count = 0
    for i in range(num_sampled):
        for j in range(i + 1, num_sampled):
            # Symmetric difference counts edges present in one but not both
            sym_diff = len(edge_sets[i].symmetric_difference(edge_sets[j]))
            # Normalise: each missing/extra edge contributes to both sides → divide by 2
            total_diff += (sym_diff / 2.0) / max_edges
            pair_count += 1

    if pair_count == 0:
        return 0.0

    avg_diversity = total_diff / float(pair_count)
    return round(min(1.0, max(0.0, avg_diversity)), 4)


def calculate_fitness_improvement(
    previous_best_fitness: float,
    current_best_fitness: float,
) -> float:
    """Calculate the normalised single-generation fitness improvement.

    Measures what fraction of the previous best fitness value was recovered in
    this generation.  A positive value means the solution improved; zero means
    no change or degradation.

    Formula
    -------
    .. math::
        \\text{improvement} = \\frac{f_{t-1} - f_t}{|f_{t-1}|}

    Clamped to :math:`[0.0, 1.0]` so that large jumps are treated uniformly.

    Parameters
    ----------
    previous_best_fitness:
        Best (lowest) fitness observed at the *previous* generation.
        Pass ``float('inf')`` for the first generation.
    current_best_fitness:
        Best (lowest) fitness observed at the *current* generation.

    Returns
    -------
    float
        Improvement ratio in **[0.0, 1.0]**.
        Returns ``0.0`` when ``previous_best_fitness`` is infinite or zero.

    Complexity
    ----------
    Time : O(1).
    Space: O(1).
    """
    # Guard: no valid baseline to compare against
    if math.isinf(previous_best_fitness) or math.isnan(previous_best_fitness):
        return 0.0

    denom = abs(previous_best_fitness)
    if denom < 1e-9:
        return 0.0

    raw_improvement = (previous_best_fitness - current_best_fitness) / denom
    clamped = max(0.0, min(1.0, raw_improvement))
    return round(clamped, 4)


def calculate_recovery_generations(
    history_fitness: List[float],
    pre_disruption_fitness: float,
    disruption_index: int,
    tolerance: float = 0.05,
) -> Optional[int]:
    """Count how many generations it took to recover to pre-disruption fitness.

    Scans the recorded best-fitness history from ``disruption_index`` onward
    and returns the first generation index (relative to the disruption) at
    which the best fitness is within ``tolerance * 100``% of the
    pre-disruption baseline.

    Parameters
    ----------
    history_fitness:
        Ordered list of best-fitness values, one entry per generation.
    pre_disruption_fitness:
        The best fitness observed *immediately before* the disruption occurred.
    disruption_index:
        Index into ``history_fitness`` at which the disruption was applied.
    tolerance:
        Fractional recovery threshold (default ``0.05`` → within 5%).

    Returns
    -------
    int or None
        Number of generations elapsed until recovery, or ``None`` if the
        optimiser did not recover within the remaining history.

    Complexity
    ----------
    Time : O(G) where G = len(history_fitness) - disruption_index.
    Space: O(1).
    """
    if not history_fitness or disruption_index >= len(history_fitness):
        return None

    target = pre_disruption_fitness * (1.0 + tolerance)
    for offset, fitness in enumerate(history_fitness[disruption_index:]):  # O(G)
        if fitness <= target:
            return offset

    return None  # Did not recover within recorded history
