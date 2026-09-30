"""
Population initialisation for AdaptIQ-R.

Generates a starting pool of candidate route permutations.  Each individual
is a permutation of customer node IDs (the depot is excluded and re-attached
during fitness evaluation).  The first individual preserves the natural
ordering; subsequent individuals are independently shuffled.

Complexity
----------
initialize_population : O(N * L) where N = population_size, L = len(customer_ids).
"""

from __future__ import annotations

import random
from typing import List, Optional

__all__ = ["initialize_population"]


def initialize_population(
    customer_ids: List[int],
    population_size: int = 100,
    rng: Optional[random.Random] = None,
) -> List[List[int]]:
    """Create an initial population of random customer-visit permutations.

    Each individual encodes a candidate ordering of delivery stops (depot
    excluded).  The depot is prepended/appended automatically during fitness
    evaluation in :class:`FitnessEngine`.

    The first individual preserves the natural (ascending ID) sequence so
    the seeded population always contains at least one deterministic baseline
    chromosome.  All remaining individuals are independently shuffled using
    the Fisher-Yates algorithm (via ``random.shuffle``).

    Parameters
    ----------
    customer_ids:
        Ordered list of all customer node IDs to include in every chromosome.
        Depot node should be excluded — it is injected during fitness decoding.
    population_size:
        Number of individuals in the initial population.  Must be ≥ 1.
    rng:
        Optional seeded :class:`random.Random` instance for reproducibility.
        If ``None``, a default (unseeded) instance is used.

    Returns
    -------
    List[List[int]]
        Population array of shape ``(population_size, len(customer_ids))``.
        Each row is a valid permutation of ``customer_ids``.

    Examples
    --------
    >>> pop = initialize_population([1, 2, 3], population_size=3, rng=random.Random(0))
    >>> len(pop)
    3
    >>> set(pop[0]) == {1, 2, 3}
    True

    Complexity
    ----------
    Time : O(N * L) — N Fisher-Yates shuffles of length-L arrays.
    Space: O(N * L) — stores all N chromosomes explicitly.
    """
    if rng is None:
        rng = random.Random()

    # Base chromosome — natural ordering provides a deterministic start point
    base: List[int] = list(customer_ids)
    population: List[List[int]] = [list(base)]  # Individual 0: unshuffled baseline

    # Individuals 1 … (population_size - 1): independent random permutations
    # Each shuffle is O(L) via Fisher-Yates — total O(N * L)
    for _ in range(population_size - 1):
        ind: List[int] = list(base)
        rng.shuffle(ind)  # O(L) in-place Fisher-Yates
        population.append(ind)

    return population
