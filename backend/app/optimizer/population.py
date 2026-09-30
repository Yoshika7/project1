"""
Population initialization and representation for AdaptIQ-R.
Represents candidate solutions as permutations of customer stops.
"""

import random
from typing import List, Dict
from backend.app.core.models import NodeModel


def initialize_population(
    customer_ids: List[int],
    population_size: int = 100,
    rng: random.Random = None
) -> List[List[int]]:
    """
    Initializes a population of candidate permutation routes.
    Guarantees every individual is a valid permutation containing each customer stop exactly once.
    """
    if rng is None:
        rng = random.Random()

    population: List[List[int]] = []
    base_chromosome = list(customer_ids)

    # 1. First individual: baseline sequence
    population.append(list(base_chromosome))

    # 2. Add randomized permutations
    for _ in range(population_size - 1):
        ind = list(base_chromosome)
        rng.shuffle(ind)
        population.append(ind)

    return population
