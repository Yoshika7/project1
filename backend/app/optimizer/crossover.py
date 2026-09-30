"""
Crossover operators for AdaptIQ-R.
Implements Order Crossover (OX) for sequence permutations.
"""

import random
from typing import List, Tuple


def order_crossover(
    parent1: List[int],
    parent2: List[int],
    rng: random.Random = None
) -> Tuple[List[int], List[int]]:
    """
    Executes two-point Order Crossover (OX) between two route permutations.
    Guarantees both children contain each node exactly once.
    """
    if rng is None:
        rng = random.Random()

    length = len(parent1)
    if length <= 2:
        return list(parent1), list(parent2)

    # Choose two distinct crossover points
    pt1, pt2 = sorted(rng.sample(range(length), 2))

    def _ox_single(p1: List[int], p2: List[int]) -> List[int]:
        child = [-1] * length
        # Copy the slice from p1
        child[pt1:pt2 + 1] = p1[pt1:pt2 + 1]
        copied_set = set(child[pt1:pt2 + 1])

        # Fill remaining slots using p2 in circular order starting after pt2
        p2_idx = (pt2 + 1) % length
        child_idx = (pt2 + 1) % length

        while -1 in child:
            candidate = p2[p2_idx]
            if candidate not in copied_set:
                child[child_idx] = candidate
                copied_set.add(candidate)
                child_idx = (child_idx + 1) % length
            p2_idx = (p2_idx + 1) % length

        return child

    child1 = _ox_single(parent1, parent2)
    child2 = _ox_single(parent2, parent1)

    return child1, child2
