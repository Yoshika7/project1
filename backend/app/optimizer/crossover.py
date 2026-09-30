"""
Order Crossover (OX-1) operator for AdaptIQ-R.

Implements the classic Order Crossover operator for permutation-encoded
chromosomes.  OX-1 preserves the relative visitation order of customer nodes
from both parents while guaranteeing that each customer appears exactly once
in each child — a critical constraint for valid Vehicle Routing Problem
solutions.

Algorithm (for child inheriting from parent1 with filler from parent2)
-----------------------------------------------------------------------
1. Select two random crossover points ``pt1`` and ``pt2`` (pt1 < pt2).
2. Copy the sub-sequence ``parent1[pt1:pt2+1]`` directly into the child.
3. Fill remaining positions in circular order (starting after ``pt2``)
   with elements from ``parent2`` that are not already in the child.

This process is applied twice (swapping parent roles) to produce two children.

Reference: Davis, L. (1985). Applying adaptive algorithms to epistatic domains.
           Proceedings of IJCAI, 162–164.

Complexity
----------
order_crossover : O(L) — single pass through each parent sequence.
"""

from __future__ import annotations

import random
from typing import List, Optional, Set, Tuple

__all__ = ["order_crossover"]


def order_crossover(
    parent1: List[int],
    parent2: List[int],
    rng: Optional[random.Random] = None,
) -> Tuple[List[int], List[int]]:
    """Apply Order Crossover (OX-1) to produce two offspring permutations.

    Generates two children by exchanging sub-sequences between ``parent1``
    and ``parent2`` while preserving the relative order of non-copied elements.
    Both children are guaranteed to be valid permutations containing every
    element of the parents exactly once.

    Parameters
    ----------
    parent1:
        First parent chromosome — a permutation of customer node IDs.
    parent2:
        Second parent chromosome — must be a permutation of the same elements
        as ``parent1``.
    rng:
        Seeded :class:`random.Random` instance for reproducibility.
        If ``None``, a default (non-reproducible) instance is used.

    Returns
    -------
    Tuple[List[int], List[int]]
        ``(child1, child2)`` — two new chromosomes.  ``child1`` inherits its
        core segment from ``parent1``; ``child2`` inherits from ``parent2``.

    Notes
    -----
    For chromosomes of length ≤ 2, the function returns copies of the parents
    unchanged (no meaningful crossover point exists).

    Examples
    --------
    >>> p1 = [1, 2, 3, 4, 5]
    >>> p2 = [5, 4, 3, 2, 1]
    >>> c1, c2 = order_crossover(p1, p2, rng=random.Random(7))
    >>> set(c1) == set(p1)   # Child must contain all elements
    True
    >>> len(set(c1)) == len(c1)  # No duplicates
    True

    Complexity
    ----------
    Time : O(L) per child — one circular scan of parent2 for each child.
    Space: O(L) — child buffer + copied-set for duplicate tracking.
    """
    if rng is None:
        rng = random.Random()

    length: int = len(parent1)
    if length <= 2:
        # No meaningful crossover possible — return copies unchanged
        return list(parent1), list(parent2)

    # Pick two distinct cut points uniformly — O(1)
    pt1, pt2 = sorted(rng.sample(range(length), 2))

    def _ox_single(p1: List[int], p2: List[int]) -> List[int]:
        """Produce one OX child inheriting the segment p1[pt1:pt2+1].

        Parameters
        ----------
        p1:
            Donor parent — contributes the core segment.
        p2:
            Filler parent — provides remaining elements in relative order.

        Returns
        -------
        List[int]
            Child chromosome — valid permutation of p1's elements.

        Complexity
        ----------
        Time : O(L) — single circular scan of p2.
        Space: O(L) — child buffer + O(segment length) for the copied set.
        """
        # Initialise child with sentinel -1 (unfilled positions)
        child: List[int] = [-1] * length

        # Step 1: Copy the inherited segment from p1 — O(pt2 - pt1)
        child[pt1 : pt2 + 1] = p1[pt1 : pt2 + 1]
        copied: Set[int] = set(child[pt1 : pt2 + 1])

        # Step 2: Fill remaining positions circularly from p2 — O(L)
        p2_idx: int = (pt2 + 1) % length     # Start reading p2 after the segment
        child_idx: int = (pt2 + 1) % length  # Start filling child after the segment

        while -1 in child:
            candidate: int = p2[p2_idx]
            if candidate not in copied:
                child[child_idx] = candidate
                copied.add(candidate)
                child_idx = (child_idx + 1) % length
            p2_idx = (p2_idx + 1) % length

        return child

    child1: List[int] = _ox_single(parent1, parent2)
    child2: List[int] = _ox_single(parent2, parent1)

    return child1, child2
