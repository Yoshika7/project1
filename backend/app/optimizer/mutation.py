"""
Mutation operators for AdaptIQ-R.
Implements Swap Mutation with dynamic probability and exploration-driven perturbation.
"""

import random
from typing import List


def swap_mutation(
    chromosome: List[int],
    mutation_rate: float,
    exploration_level: float = 0.5,
    rng: random.Random = None
) -> List[int]:
    """
    Applies swap mutation to a chromosome.
    If rng.random() < mutation_rate, performs index swaps.
    Under high exploration, increases perturbation intensity (multi-swap or 2-opt inversion).
    """
    if rng is None:
        rng = random.Random()

    result = list(chromosome)
    length = len(result)
    if length <= 1:
        return result

    # Check if mutation activates for this individual
    if rng.random() < mutation_rate:
        # Number of swaps scales with exploration level: 1 to 3 swaps
        num_swaps = 1
        if exploration_level > 0.65:
            num_swaps = 2 if rng.random() < 0.7 else 3
        elif exploration_level > 0.45:
            num_swaps = 2 if rng.random() < 0.4 else 1

        for _ in range(num_swaps):
            i, j = rng.sample(range(length), 2)
            result[i], result[j] = result[j], result[i]

        # Inversion mutation under extreme exploration
        if exploration_level > 0.8 and rng.random() < 0.3:
            pt1, pt2 = sorted(rng.sample(range(length), 2))
            result[pt1:pt2 + 1] = reversed(result[pt1:pt2 + 1])

    return result
