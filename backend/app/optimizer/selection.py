"""
Tournament selection operator for AdaptIQ-R.

Implements dynamic-pressure tournament selection where selection intensity
is continuously modulated by the Mamdani fuzzy controller's exploration output.

Design rationale
----------------
Classical tournament selection uses a fixed tournament size k.  Larger k
increases selection pressure (exploitation); smaller k reduces it (exploration).
In AdaptIQ-R, k is computed from the fuzzy exploration_level output each
generation, creating a *coordinated* adaptation: when the fuzzy controller
detects low diversity and high disruption severity, it simultaneously increases
mutation rate AND reduces selection pressure — both responses encourage
exploration of the route search space.

Complexity
----------
tournament_selection : O(k) — k random samples + k fitness lookups.
"""

from __future__ import annotations

import random
from typing import List, Optional

__all__ = ["tournament_selection"]


def tournament_selection(
    population: List[List[int]],
    fitnesses: List[float],
    tournament_size: int = 3,
    exploration_level: float = 0.5,
    rng: Optional[random.Random] = None,
) -> List[int]:
    """Select one parent chromosome via exploration-adaptive tournament selection.

    Draws ``k`` candidates uniformly at random from ``population`` and returns
    the one with the lowest fitness (minimisation).  The effective tournament
    size ``k`` is overridden by ``exploration_level`` to implement dynamic
    selection pressure:

    .. math::

        k_{\\text{eff}} = \\text{clip}\\left(\\lfloor 5 - 3 \\cdot
        \\text{exploration\\_level} \\rfloor,\\ 2,\\ 5\\right)

    High exploration (≈ 0.9) → k_eff = 2 → weak pressure → diversity preserved.
    Low exploration (≈ 0.1)  → k_eff = 5 → strong pressure → exploitation.

    A small stochastic escape (10 % probability when exploration_level > 0.6)
    randomly selects among tournament contestants to avoid early fixation.

    Parameters
    ----------
    population:
        Current generation — list of chromosome permutations.
    fitnesses:
        Fitness scores corresponding 1-to-1 with ``population``.
        Lower scores are better (minimisation objective).
    tournament_size:
        Nominal tournament size.  Overridden by ``exploration_level`` in
        practice; kept for API compatibility.
    exploration_level:
        Fuzzy controller exploration output in ``[0.0, 1.0]``.
        High values → smaller tournament (more exploration).
    rng:
        Seeded :class:`random.Random` instance.  If ``None``, a default
        instance is used (non-reproducible).

    Returns
    -------
    List[int]
        A copy of the winning chromosome (safe to mutate without affecting
        the original population array).

    Raises
    ------
    ValueError
        If ``population`` is empty.

    Examples
    --------
    >>> pop = [[1, 2], [2, 1], [1, 2]]
    >>> fits = [0.9, 0.3, 0.6]
    >>> winner = tournament_selection(pop, fits, rng=random.Random(0))
    >>> fits[pop.index(winner)]  # Should be the best (lowest) fitness
    0.3

    Complexity
    ----------
    Time : O(k) — k random samples from range(pop_size) + k fitness comparisons.
    Space: O(k) — list of k candidate indices.
    """
    if rng is None:
        rng = random.Random()

    pop_size: int = len(population)
    if pop_size == 0:
        raise ValueError("Population cannot be empty.")

    # Dynamic tournament size: k ∈ [2, 5] derived from exploration level
    # High exploration_level → low k (weak pressure → diverse selection)
    effective_k: int = max(2, min(5, int(round(5.0 - 3.0 * exploration_level))))
    k: int = min(effective_k, pop_size)

    # Draw k unique candidate indices uniformly at random — O(k)
    candidate_indices: List[int] = rng.sample(range(pop_size), k)

    # Greedy selection: pick the candidate with minimum fitness — O(k)
    best_idx: int = min(candidate_indices, key=lambda idx: fitnesses[idx])

    # Stochastic escape: 10–18 % chance of random pick under high exploration
    # Prevents all runs converging to identical parents in low-diversity states
    if exploration_level > 0.6 and rng.random() < (exploration_level * 0.2):
        best_idx = rng.choice(candidate_indices)

    # Return a defensive copy — caller may mutate the result freely
    return list(population[best_idx])
