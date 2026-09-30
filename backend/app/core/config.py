"""
Global configuration defaults for AdaptIQ-R.
All parameters can be overridden per experiment or API request.
"""

from typing import Dict, Tuple

# Default Fitness Weights
DEFAULT_DISTANCE_WEIGHT = 0.45
DEFAULT_TIME_WEIGHT = 0.35
DEFAULT_PENALTY_WEIGHT = 0.20

# GA Defaults
DEFAULT_POPULATION_SIZE = 100
DEFAULT_GENERATIONS = 200
DEFAULT_ELITE_RATIO = 0.05
DEFAULT_CROSSOVER_RATE = 0.85
DEFAULT_MUTATION_RATE = 0.15
DEFAULT_TOURNAMENT_SIZE = 3
DEFAULT_STAGNATION_LIMIT = 40

# Disruption Severity Weights (Specified in Section 5 of user requirements)
# S = 0.40 * blocked_edge_ratio + 0.30 * normalized_traffic_change + 0.15 * normalized_priority_change + 0.15 * vehicle_change
SEVERITY_WEIGHT_BLOCKED = 0.40
SEVERITY_WEIGHT_TRAFFIC = 0.30
SEVERITY_WEIGHT_PRIORITY = 0.15
SEVERITY_WEIGHT_VEHICLE = 0.15

# Constraint Penalties
PENALTY_UNREACHABLE_SEGMENT = 1000.0
PENALTY_BLOCKED_EDGE_USED = 500.0
PENALTY_PRIORITY_VIOLATION = 50.0
PENALTY_CAPACITY_VIOLATION = 100.0

# Fuzzy Parameter Ranges
MUTATION_RATE_MIN = 0.05
MUTATION_RATE_MAX = 0.45
EXPLORATION_LEVEL_MIN = 0.10
EXPLORATION_LEVEL_MAX = 0.90

# Fuzzy Membership Default Boundaries: (a, b, c) for triangular or (a, b, c, d) for trapezoidal
# Input 1: Population Diversity in [0, 1]
FUZZY_DIVERSITY_MF = {
    "LOW": (0.0, 0.0, 0.25, 0.45),      # Trapezoidal left-shoulder
    "MEDIUM": (0.25, 0.50, 0.75),       # Triangular
    "HIGH": (0.55, 0.75, 1.0, 1.0)      # Trapezoidal right-shoulder
}

# Input 2: Fitness Improvement in [0, 1]
FUZZY_IMPROVEMENT_MF = {
    "LOW": (0.0, 0.0, 0.05, 0.15),      # Trapezoidal left-shoulder
    "MEDIUM": (0.08, 0.22, 0.45),       # Triangular
    "HIGH": (0.35, 0.55, 1.0, 1.0)      # Trapezoidal right-shoulder
}

# Input 3: Disruption Severity in [0, 1]
FUZZY_SEVERITY_MF = {
    "LOW": (0.0, 0.0, 0.20, 0.35),      # Trapezoidal left-shoulder
    "MEDIUM": (0.25, 0.50, 0.75),       # Triangular
    "HIGH": (0.60, 0.80, 1.0, 1.0)      # Trapezoidal right-shoulder
}

# Output 1: Mutation Rate in [0.05, 0.45]
FUZZY_MUTATION_MF = {
    "LOW": (0.05, 0.05, 0.12, 0.20),
    "MEDIUM": (0.15, 0.25, 0.35),
    "HIGH": (0.30, 0.38, 0.45, 0.45)
}

# Output 2: Exploration Level in [0.10, 0.90]
FUZZY_EXPLORATION_MF = {
    "LOW": (0.10, 0.10, 0.25, 0.40),
    "MEDIUM": (0.30, 0.50, 0.70),
    "HIGH": (0.60, 0.75, 0.90, 0.90)
}
