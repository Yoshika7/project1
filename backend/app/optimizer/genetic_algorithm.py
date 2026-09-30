"""
Genetic Algorithm Optimizer for AdaptIQ-R.

Implements the continuous closed-loop adaptive evolutionary cycle:

    Population → Fitness Evaluation → Diversity / Improvement / Severity
    → Mamdani Fuzzy Controller → Adaptive Mutation Rate / Exploration Level
    → Tournament Selection → Order Crossover (OX) → Adaptive Swap Mutation
    → Next Generation

Supports two operating modes:
  * **AdaptIQ-R (Adaptive)**: Fuzzy controller dynamically tunes mutation rate
    and exploration level based on population state and disruption telemetry.
  * **Baseline GA (Fixed)**: Uses constant operator probabilities for fair
    benchmark comparison.

Complexity Summary
------------------
- __init__          : O(N * L log L)  — population initialisation
- notify_disruption : O(N * k * (|V| log |V| + |E|))  — full re-evaluation
- step              : O(N * k * (|V| log |V| + |E|) + N log N + S²*L)
                      where N = population size, k = route pairs,
                      S = diversity sample limit, L = route length

These are dominated by the Dijkstra calls inside FitnessEngine.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable, Dict, List, Optional

from backend.app.core.models import (
    GenerationMetric,
    NetworkScenarioModel,
    OptimizationConfig,
    RouteEvaluation,
)
from backend.app.evaluation.metrics import (
    calculate_fitness_improvement,
    calculate_population_diversity,
)
from backend.app.fuzzy.fuzzy_controller import FuzzyController
from backend.app.optimizer.crossover import order_crossover
from backend.app.optimizer.fitness import FitnessEngine
from backend.app.optimizer.mutation import swap_mutation
from backend.app.optimizer.population import initialize_population
from backend.app.optimizer.selection import tournament_selection
from backend.app.simulation.disruption_engine import DisruptionEngine

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["GeneticAlgorithmOptimizer"]


class GeneticAlgorithmOptimizer:
    """Real evolutionary route optimiser with online Mamdani Fuzzy adaptation.

    AdaptIQ-R couples a permutation-based Genetic Algorithm with a closed-loop
    Fuzzy Inference System that continuously senses population state
    (diversity, improvement rate) and environmental disruption severity to
    re-tune genetic operator probabilities on every generation.

    This differs from adaptive GAs in the literature that use hand-coded
    schedules or simple heuristics.  Here all parameter changes are driven by
    fuzzy inference over three real-valued telemetry signals.

    Attributes
    ----------
    scenario : NetworkScenarioModel
        Road network, node/edge topology, demands, and depot configuration.
    config : OptimizationConfig
        Hyperparameter bundle (population size, crossover rate, weights, etc.).
    population : List[List[int]]
        Current generation — list of customer-ID permutation chromosomes.
    generation : int
        Number of completed evolutionary steps (generations).
    history : List[GenerationMetric]
        Ordered record of per-generation telemetry (one entry per :meth:`step`).
    best_evaluation : RouteEvaluation or None
        Best route evaluation seen *since initialisation or last disruption*.
    best_fitness : float
        Cached best (lowest) fitness value for efficient stagnation detection.

    Parameters
    ----------
    scenario:
        The road network scenario to optimise routes over.
    config:
        Optimisation configuration.  Defaults to :class:`OptimizationConfig`
        with standard hyperparameters if ``None``.
    disruption_engine:
        Pre-configured disruption engine.  If ``None`` a fresh engine attached
        to ``scenario`` is created (no disruptions active).

    Raises
    ------
    ValueError
        If the scenario contains no customer stops (only a depot node).

    Complexity
    ----------
    Time : O(N * L log L) for population initialisation via Fisher-Yates shuffle.
    Space: O(N * L) for the initial population array.
    """

    def __init__(
        self,
        scenario: NetworkScenarioModel,
        config: Optional[OptimizationConfig] = None,
        disruption_engine: Optional[DisruptionEngine] = None,
    ) -> None:
        self.scenario = scenario
        self.config = config or OptimizationConfig()

        # Seeded RNG ensures reproducibility when config.seed is fixed
        self.rng = random.Random(self.config.seed)

        # ------------------------------------------------------------------ #
        # Sub-engine initialisation                                           #
        # ------------------------------------------------------------------ #
        self.fitness_engine = FitnessEngine(
            scenario=self.scenario,
            distance_weight=self.config.distance_weight,
            time_weight=self.config.time_weight,
            penalty_weight=self.config.penalty_weight,
        )
        # Use provided engine (allows pre-configured disruptions) or fresh one
        self.disruption_engine = disruption_engine or DisruptionEngine(self.scenario)
        self.fuzzy_controller = FuzzyController()

        # ------------------------------------------------------------------ #
        # Customer IDs: all nodes except depot                                #
        # ------------------------------------------------------------------ #
        self.customer_ids: List[int] = [
            nid for nid in self.scenario.nodes.keys()
            if nid != self.scenario.depot_id
        ]
        if not self.customer_ids:
            raise ValueError(
                "Scenario has no customer stops to route.  "
                "All nodes are depots or the network is empty."
            )

        # ------------------------------------------------------------------ #
        # Population — O(N * L log L) initialisation via random permutations  #
        # ------------------------------------------------------------------ #
        self.population: List[List[int]] = initialize_population(
            customer_ids=self.customer_ids,
            population_size=self.config.population_size,
            rng=self.rng,
        )

        # ------------------------------------------------------------------ #
        # Tracking state                                                      #
        # ------------------------------------------------------------------ #
        self.generation: int = 0
        self.history: List[GenerationMetric] = []
        self.best_evaluation: Optional[RouteEvaluation] = None
        self.best_fitness: float = float("inf")
        self.previous_best_fitness: float = float("inf")

        # Fuzzy controller outputs (updated per generation)
        self.current_mutation_rate: float = self.config.initial_mutation_rate
        self.current_exploration_level: float = 0.5
        self.current_diversity: float = 0.0
        self.current_improvement: float = 0.0
        self.current_severity: float = 0.0
        self.activated_rules: List[str] = []

        # Stagnation counter — incremented each generation without improvement
        self.generations_since_improvement: int = 0

    # ---------------------------------------------------------------------- #
    # Public interface                                                        #
    # ---------------------------------------------------------------------- #

    def notify_disruption(self) -> None:
        """React to a mid-run environmental disruption.

        Call this immediately after applying any change to the disruption engine
        (e.g., ``block_road``, ``surge_traffic``).  This method:

        1. Invalidates the fitness engine's path cache so Dijkstra re-runs on
           the updated graph topology.  **O(1)**
        2. Re-evaluates every individual in the current population under the
           new conditions.  **O(N * k * (|V| log |V| + |E|))**
        3. Updates ``best_fitness`` and ``best_evaluation`` to reflect the new
           post-disruption landscape.
        4. Resets ``generations_since_improvement`` so stagnation detection
           restarts cleanly from the disruption point.

        Complexity
        ----------
        Time : O(N * k * (|V| log |V| + |E|)) — dominated by N Dijkstra calls.
        Space: O(N) for re-evaluation results list.
        """
        # Step 1 — invalidate cached shortest paths (O(1))
        self.fitness_engine.invalidate_cache()

        # Step 2 — re-evaluate entire population under new graph state
        evaluations: List[RouteEvaluation] = [
            self.fitness_engine.evaluate_route(ind) for ind in self.population
        ]

        # Step 3 — update best known solution
        best_idx: int = min(
            range(len(evaluations)), key=lambda i: evaluations[i].fitness
        )
        self.best_evaluation = evaluations[best_idx]
        self.best_fitness = self.best_evaluation.fitness
        self.previous_best_fitness = self.best_fitness

        # Step 4 — reset stagnation counter at disruption boundary
        self.generations_since_improvement = 0

    def step(self) -> GenerationMetric:
        """Execute one full generation of the adaptive evolutionary cycle.

        The cycle follows these ordered phases:

        1. **Fitness Evaluation** — score every individual via
           :meth:`FitnessEngine.evaluate_route`.  O(N * Dijkstra)
        2. **Population Statistics** — compute best, average, worst fitness.
           O(N)
        3. **Diversity Calculation** — sampled pairwise edge-set comparison.
           O(S² * L)
        4. **Improvement Rate** — normalised delta from previous generation.
           O(1)
        5. **Disruption Severity** — live read from DisruptionEngine.  O(1)
        6. **Fuzzy Adaptation** (AdaptIQ-R mode only) — Mamdani inference
           updates mutation rate and exploration level.  O(R * D) where
           R = number of rules, D = defuzzification steps (fixed = 100).
        7. **Next Population** — elitism, tournament selection, OX crossover,
           adaptive swap mutation.  O(N log N + N * L)
        8. **Metric Recording** — append :class:`GenerationMetric` to history.
           O(1)

        Returns
        -------
        GenerationMetric
            Complete telemetry snapshot of this generation.

        Complexity
        ----------
        Time : O(N * k * (|V| log|V| + |E|) + N log N + S² * L)
        Space: O(N * L) for next population array.
        """
        self.generation += 1
        gen_start: float = time.perf_counter()

        # ------------------------------------------------------------------ #
        # Phase 1: Fitness Evaluation — O(N * Dijkstra)                      #
        # ------------------------------------------------------------------ #
        evaluations: List[RouteEvaluation] = [
            self.fitness_engine.evaluate_route(ind) for ind in self.population
        ]
        fitness_scores: List[float] = [ev.fitness for ev in evaluations]

        # ------------------------------------------------------------------ #
        # Phase 2: Population Statistics — O(N)                              #
        # ------------------------------------------------------------------ #
        best_idx: int = min(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
        current_best_eval: RouteEvaluation = evaluations[best_idx]
        current_best_fit: float = current_best_eval.fitness
        avg_fit: float = round(sum(fitness_scores) / len(fitness_scores), 4)
        worst_fit: float = round(max(fitness_scores), 4)

        # ------------------------------------------------------------------ #
        # Phase 3: Diversity — O(S² * L), S ≤ 30 (bounded constant)         #
        # ------------------------------------------------------------------ #
        self.current_diversity = calculate_population_diversity(
            self.population, sample_limit=30, seed=self.generation
        )

        # ------------------------------------------------------------------ #
        # Phase 4: Fitness Improvement — O(1)                                #
        # ------------------------------------------------------------------ #
        self.current_improvement = calculate_fitness_improvement(
            self.previous_best_fitness,
            current_best_fit,
        )

        # Stagnation tracking — reset counter when improvement exceeds threshold
        if current_best_fit < self.best_fitness - self.config.convergence_threshold:
            self.best_fitness = current_best_fit
            self.best_evaluation = current_best_eval
            self.generations_since_improvement = 0
        else:
            self.generations_since_improvement += 1

        self.previous_best_fitness = current_best_fit

        # ------------------------------------------------------------------ #
        # Phase 5: Disruption Severity — O(1)                                #
        # ------------------------------------------------------------------ #
        sev_obj = self.disruption_engine.calculate_severity()
        self.current_severity = sev_obj.severity

        # ------------------------------------------------------------------ #
        # Phase 6: Mamdani Fuzzy Adaptation (AdaptIQ-R mode only)            #
        # Fixed parameters used in Baseline GA for fair comparison           #
        # ------------------------------------------------------------------ #
        if self.config.is_adaptive:
            # Fuzzy inference: O(R * D) — R rules, D=100 defuzzification steps
            fuzzy_res: Dict[str, Any] = self.fuzzy_controller.evaluate(
                diversity=self.current_diversity,
                improvement=self.current_improvement,
                severity=self.current_severity,
            )
            self.current_mutation_rate = fuzzy_res["mutation_rate"]
            self.current_exploration_level = fuzzy_res["exploration_level"]
            self.activated_rules = fuzzy_res["activated_rules"]
        else:
            # Baseline GA: fixed hyperparameters — no fuzzy adaptation
            self.current_mutation_rate = self.config.initial_mutation_rate
            self.current_exploration_level = 0.5  # Neutral exploration
            self.activated_rules = []

        # ------------------------------------------------------------------ #
        # Phase 7: Next Population — O(N log N) sort + O(N * L) breeding     #
        # ------------------------------------------------------------------ #
        pop_size: int = len(self.population)
        elite_count: int = max(1, int(round(pop_size * self.config.elite_ratio)))

        # O(N log N) — sort indices by ascending fitness (lower = better)
        sorted_indices: List[int] = sorted(
            range(pop_size), key=lambda i: fitness_scores[i]
        )

        # Elitism: copy top-k individuals unchanged into next generation
        new_population: List[List[int]] = [
            list(self.population[idx]) for idx in sorted_indices[:elite_count]
        ]

        # Breeding loop — O(N * L) total (OX crossover + swap mutation)
        while len(new_population) < pop_size:
            # Tournament selection — dynamic pressure via exploration_level
            parent1: List[int] = tournament_selection(
                population=self.population,
                fitnesses=fitness_scores,
                tournament_size=self.config.tournament_size,
                exploration_level=self.current_exploration_level,
                rng=self.rng,
            )
            parent2: List[int] = tournament_selection(
                population=self.population,
                fitnesses=fitness_scores,
                tournament_size=self.config.tournament_size,
                exploration_level=self.current_exploration_level,
                rng=self.rng,
            )

            # Order Crossover (OX-1) — preserves relative visit order — O(L)
            if self.rng.random() < self.config.crossover_rate:
                child1, child2 = order_crossover(parent1, parent2, rng=self.rng)
            else:
                child1, child2 = list(parent1), list(parent2)

            # Adaptive Swap Mutation — number of swaps scales with exploration — O(L)
            child1 = swap_mutation(
                chromosome=child1,
                mutation_rate=self.current_mutation_rate,
                exploration_level=self.current_exploration_level,
                rng=self.rng,
            )
            child2 = swap_mutation(
                chromosome=child2,
                mutation_rate=self.current_mutation_rate,
                exploration_level=self.current_exploration_level,
                rng=self.rng,
            )

            new_population.append(child1)
            if len(new_population) < pop_size:
                new_population.append(child2)

        self.population = new_population

        # ------------------------------------------------------------------ #
        # Phase 8: Record Generation Metric — O(1)                           #
        # ------------------------------------------------------------------ #
        elapsed_ms: float = round((time.perf_counter() - gen_start) * 1000.0, 2)

        metric = GenerationMetric(
            generation=self.generation,
            best_fitness=current_best_fit,
            avg_fitness=avg_fit,
            worst_fitness=worst_fit,
            population_diversity=self.current_diversity,
            fitness_improvement=self.current_improvement,
            disruption_severity=self.current_severity,
            mutation_rate=self.current_mutation_rate,
            exploration_level=self.current_exploration_level,
            activated_rules=list(self.activated_rules),
            best_route=current_best_eval.node_sequence,
            detailed_path=current_best_eval.detailed_path,
            is_feasible=current_best_eval.is_feasible,
            total_distance=current_best_eval.total_distance,
            total_travel_time=current_best_eval.total_travel_time,
            constraint_penalty=current_best_eval.constraint_penalty,
        )
        self.history.append(metric)
        return metric

    def run(
        self,
        generations: int,
        callback: Optional[Callable[[GenerationMetric], None]] = None,
    ) -> List[GenerationMetric]:
        """Run the optimizer for a fixed number of generations.

        Parameters
        ----------
        generations:
            Number of evolutionary steps to execute.
        callback:
            Optional callable invoked after every generation with the
            :class:`GenerationMetric` for that generation (useful for
            streaming results to a UI or logging system).

        Returns
        -------
        List[GenerationMetric]
            Ordered list of per-generation metrics produced during this run.

        Complexity
        ----------
        Time : O(generations * step_cost) — see :meth:`step` for step_cost.
        Space: O(generations) for the returned metrics list.
        """
        new_metrics: List[GenerationMetric] = []
        for _ in range(generations):
            m = self.step()
            new_metrics.append(m)
            if callback is not None:
                callback(m)
        return new_metrics
