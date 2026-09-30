"""
Selection operators for AdaptIQ-R.
Implements Tournament Selection with dynamic pressure modulated by exploration level.
"""

import random
from typing import List, Tuple


def tournament_selection(
    population: List[List[int]],
    fitnesses: List[float],
    tournament_size: int = 3,
    exploration_level: float = 0.5,
    rng: random.Random = None
) -> List[int]:
    """
    Selects one parent from the population using tournament selection.
    Tournament size and selection pressure dynamically adapt with exploration_level:
    - High exploration (e.g. 0.8): smaller tournament (k=2) to preserve diversity.
    - Low exploration (e.g. 0.2): larger tournament (k=4-5) for strong exploitation.
    """
    if rng is None:
        rng = random.Random()

    pop_size = len(population)
    if pop_size == 0:
        raise ValueError("Population cannot be empty.")

    # Dynamically scale tournament size: k in [2, 5]
    effective_k = max(2, min(5, int(round(5.0 - 3.0 * exploration_level))))
    k = min(effective_k, pop_size)

    # Pick k candidates uniformly at random
    candidate_indices = rng.sample(range(pop_size), k)

    # Pick candidate with the lowest fitness (minimization)
    best_idx = min(candidate_indices, key=lambda idx: fitnesses[idx])

    # With high exploration, there is a small chance (10%) to choose a random contestant to explore
    if exploration_level > 0.6 and rng.random() < (exploration_level * 0.2):
        best_idx = rng.choice(candidate_indices)

    return list(population[best_idx])
