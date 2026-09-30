"""
Adaptive Swap Mutation operator for AdaptIQ-R.

Implements a multi-swap / inversion mutation operator whose structural
intensity scales with the Mamdani fuzzy controller's exploration_level output.

Key innovation (vs classical adaptive mutation)
-----------------------------------------------
Classical adaptive mutation operators adjust the *probability* that an
individual is mutated.  AdaptIQ-R's swap mutation adjusts the *number of
simultaneous position swaps* per mutated individual.  This controls the
search radius in permutation space:

* Low exploration (≈ 0.1)  → 1 swap  → small neighbourhood, fine-grained search
* Med exploration (≈ 0.5)  → 1–2 swaps → balanced
* High exploration (≈ 0.9) → 2–3 swaps + possible 2-opt inversion → wide jump

Under extreme disruption (exploration_level > 0.8), a 2-opt segment inversion
is additionally applied with 30 % probability, generating larger structural
perturbations to escape infeasibility basins.

Complexity
----------
swap_mutation : O(L) — at most O(L) for the inversion, O(1) for swaps.
"""

from __future__ import annotations

import random
from typing import List, Optional

__all__ = ["swap_mutation"]


def swap_mutation(
    chromosome: List[int],
    mutation_rate: float,
    exploration_level: float = 0.5,
    rng: Optional[random.Random] = None,
) -> List[int]:
    """Apply adaptive swap mutation to a chromosome.

    With probability ``mutation_rate``, performs one or more random position
    swaps on a copy of ``chromosome``.  The number of swaps is controlled by
    ``exploration_level`` so that the fuzzy controller can modulate both
    mutation rate and structural perturbation magnitude simultaneously.

    Under extreme exploration conditions (``exploration_level > 0.8``), a
    2-opt segment inversion is applied with 30 % probability to generate
    large-scale structural rearrangements — useful for escaping infeasibility
    basins after severe disruptions (e.g., road block cuts the graph).

    Parameters
    ----------
    chromosome:
        Input chromosome to (possibly) mutate — a permutation of customer IDs.
        Not modified in-place; a copy is always returned.
    mutation_rate:
        Probability in ``[0, 1]`` that this individual undergoes mutation.
        Provided by the Mamdani fuzzy controller in adaptive mode.
    exploration_level:
        Fuzzy exploration output in ``[0, 1]`` that controls mutation magnitude.
        High values → more simultaneous swaps → wider neighbourhood search.
    rng:
        Seeded :class:`random.Random` instance for reproducibility.
        If ``None``, a default instance is used.

    Returns
    -------
    List[int]
        Mutated chromosome (or unmodified copy if mutation did not activate).

    Examples
    --------
    >>> ch = [1, 2, 3, 4, 5]
    >>> mutated = swap_mutation(ch, mutation_rate=1.0, exploration_level=0.9, rng=random.Random(0))
    >>> set(mutated) == set(ch)   # All elements preserved
    True
    >>> len(set(mutated)) == len(mutated)  # No duplicates
    True

    Complexity
    ----------
    Time : O(L) — dominated by the optional 2-opt inversion step.
    Space: O(L) — working copy of the chromosome.
    """
    if rng is None:
        rng = random.Random()

    # Always work on a copy — never mutate the caller's chromosome
    result: List[int] = list(chromosome)
    length: int = len(result)
    if length <= 1:
        return result  # Cannot meaningfully mutate a trivial chromosome

    # Gate: mutation fires probabilistically based on fuzzy mutation_rate
    if rng.random() >= mutation_rate:
        return result  # No mutation this individual

    # ------------------------------------------------------------------ #
    # Step 1: Determine number of swaps based on exploration level         #
    # Low exploration  → 1 swap (exploit fine local neighbourhood)         #
    # Med exploration  → 1–2 swaps (balanced)                             #
    # High exploration → 2–3 swaps (wide neighbourhood jump)              #
    # ------------------------------------------------------------------ #
    if exploration_level > 0.65:
        # High exploration: 2 swaps with 70 % probability, else 3 swaps
        num_swaps: int = 2 if rng.random() < 0.7 else 3
    elif exploration_level > 0.45:
        # Medium exploration: 2 swaps with 40 % probability, else 1 swap
        num_swaps = 2 if rng.random() < 0.4 else 1
    else:
        # Low exploration: single swap for fine-grained local search
        num_swaps = 1

    # Apply the computed number of random position swaps — O(num_swaps) ≤ O(1)
    for _ in range(num_swaps):
        i, j = rng.sample(range(length), 2)
        result[i], result[j] = result[j], result[i]

    # ------------------------------------------------------------------ #
    # Step 2: Optional 2-opt inversion under extreme exploration           #
    # Generates a segment reversal for large structural rearrangement      #
    # Useful after severe disruptions that sever critical route segments   #
    # ------------------------------------------------------------------ #
    if exploration_level > 0.8 and rng.random() < 0.3:
        pt1, pt2 = sorted(rng.sample(range(length), 2))
        # In-place reversal of result[pt1:pt2+1] — O(pt2 - pt1) ≤ O(L)
        result[pt1 : pt2 + 1] = result[pt1 : pt2 + 1][::-1]

    return result
