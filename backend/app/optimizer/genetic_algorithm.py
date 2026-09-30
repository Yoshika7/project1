"""
Genetic Algorithm Optimizer for AdaptIQ-R.
Implements the continuous closed-loop adaptive evolutionary cycle:
Population -> Evaluation -> Diversity/Improvement/Severity -> Fuzzy Logic ->
Adaptive Mutation/Exploration -> Selection/Crossover/Mutation -> Next Generation.
Supports both AdaptIQ-R (Fuzzy Adaptive) and Baseline GA (Fixed Parameters).
"""

import random
import time
from typing import List, Optional, Callable, Dict, Any

from backend.app.core.models import (
    NetworkScenarioModel,
    OptimizationConfig,
    GenerationMetric,
    RouteEvaluation
)
from backend.app.optimizer.population import initialize_population
from backend.app.optimizer.fitness import FitnessEngine
from backend.app.optimizer.selection import tournament_selection
from backend.app.optimizer.crossover import order_crossover
from backend.app.optimizer.mutation import swap_mutation
from backend.app.fuzzy.fuzzy_controller import FuzzyController
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.evaluation.metrics import (
    calculate_population_diversity,
    calculate_fitness_improvement
)


class GeneticAlgorithmOptimizer:
    """
    Real Evolutionary Route Optimizer with Fuzzy Adaptation.
    """

    def __init__(
        self,
        scenario: NetworkScenarioModel,
        config: Optional[OptimizationConfig] = None,
        disruption_engine: Optional[DisruptionEngine] = None
    ):
        self.scenario = scenario
        self.config = config or OptimizationConfig()
        self.rng = random.Random(self.config.seed)

        self.fitness_engine = FitnessEngine(
            scenario=self.scenario,
            distance_weight=self.config.distance_weight,
            time_weight=self.config.time_weight,
            penalty_weight=self.config.penalty_weight
        )
        self.disruption_engine = disruption_engine or DisruptionEngine(self.scenario)
        self.fuzzy_controller = FuzzyController()

        # Customer stop indices (excluding depot 0)
        self.customer_ids = [nid for nid in self.scenario.nodes.keys() if nid != self.scenario.depot_id]
        if not self.customer_ids:
            raise ValueError("Scenario has no customer stops to route.")

        # Initialize Population
        self.population: List[List[int]] = initialize_population(
            customer_ids=self.customer_ids,
            population_size=self.config.population_size,
            rng=self.rng
        )

        self.generation = 0
        self.history: List[GenerationMetric] = []
        self.best_evaluation: Optional[RouteEvaluation] = None
        self.best_fitness = float("inf")
        self.previous_best_fitness = float("inf")

        # Dynamic state parameters
        self.current_mutation_rate = self.config.initial_mutation_rate
        self.current_exploration_level = 0.5
        self.current_diversity = 0.0
        self.current_improvement = 0.0
        self.current_severity = 0.0
        self.activated_rules: List[str] = []

        # Stagnation monitoring
        self.generations_since_improvement = 0

    def notify_disruption(self) -> None:
        """
        Notifies optimizer that the environment has changed.
        Invalidates fitness cache, re-evaluates current population under the new conditions,
        and resets best_fitness to the new actual state.
        """
        self.fitness_engine.invalidate_cache()
        evaluations = [self.fitness_engine.evaluate_route(ind) for ind in self.population]
        best_idx = min(range(len(evaluations)), key=lambda i: evaluations[i].fitness)
        self.best_evaluation = evaluations[best_idx]
        self.best_fitness = self.best_evaluation.fitness
        self.previous_best_fitness = self.best_fitness
        self.generations_since_improvement = 0

    def step(self) -> GenerationMetric:
        """
        Executes one full generation of the evolutionary cycle.
        """
        self.generation += 1

        # 1. Fitness Evaluation
        evaluations: List[RouteEvaluation] = [
            self.fitness_engine.evaluate_route(ind) for ind in self.population
        ]
        fitness_scores = [ev.fitness for ev in evaluations]

        # 2. Identify Best, Average, and Worst
        best_idx = min(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
        current_best_eval = evaluations[best_idx]
        current_best_fit = current_best_eval.fitness
        avg_fit = round(sum(fitness_scores) / len(fitness_scores), 4)
        worst_fit = round(max(fitness_scores), 4)

        # 3. Calculate Real Population Diversity [0, 1]
        self.current_diversity = calculate_population_diversity(self.population)

        # 4. Calculate Real Fitness Improvement [0, 1]
        self.current_improvement = calculate_fitness_improvement(
            self.previous_best_fitness,
            current_best_fit
        )

        # Check for stagnation / improvement tracking
        if current_best_fit < self.best_fitness - self.config.convergence_threshold:
            self.best_fitness = current_best_fit
            self.best_evaluation = current_best_eval
            self.generations_since_improvement = 0
        else:
            self.generations_since_improvement += 1

        self.previous_best_fitness = current_best_fit

        # 5. Read Current Disruption Severity [0, 1]
        sev_obj = self.disruption_engine.calculate_severity()
        self.current_severity = sev_obj.severity

        # 6. Mamdani Fuzzy Controller Adaptation
        if self.config.is_adaptive:
            fuzzy_res = self.fuzzy_controller.evaluate(
                diversity=self.current_diversity,
                improvement=self.current_improvement,
                severity=self.current_severity
            )
            self.current_mutation_rate = fuzzy_res["mutation_rate"]
            self.current_exploration_level = fuzzy_res["exploration_level"]
            self.activated_rules = fuzzy_res["activated_rules"]
        else:
            # Baseline GA uses fixed mutation rate and neutral exploration
            self.current_mutation_rate = self.config.initial_mutation_rate
            self.current_exploration_level = 0.5
            self.activated_rules = []

        # 7. Form Next Population (Selection, OX Crossover, Mutation, Elitism)
        pop_size = len(self.population)
        elite_count = max(1, int(round(pop_size * self.config.elite_ratio)))

        # Sort population by fitness (ascending)
        sorted_indices = sorted(range(pop_size), key=lambda i: fitness_scores[i])
        new_population: List[List[int]] = [
            list(self.population[idx]) for idx in sorted_indices[:elite_count]
        ]

        # Breeding loop
        while len(new_population) < pop_size:
            parent1 = tournament_selection(
                population=self.population,
                fitnesses=fitness_scores,
                tournament_size=self.config.tournament_size,
                exploration_level=self.current_exploration_level,
                rng=self.rng
            )
            parent2 = tournament_selection(
                population=self.population,
                fitnesses=fitness_scores,
                tournament_size=self.config.tournament_size,
                exploration_level=self.current_exploration_level,
                rng=self.rng
            )

            # Crossover
            if self.rng.random() < self.config.crossover_rate:
                child1, child2 = order_crossover(parent1, parent2, rng=self.rng)
            else:
                child1, child2 = list(parent1), list(parent2)

            # Mutation
            child1 = swap_mutation(
                chromosome=child1,
                mutation_rate=self.current_mutation_rate,
                exploration_level=self.current_exploration_level,
                rng=self.rng
            )
            child2 = swap_mutation(
                chromosome=child2,
                mutation_rate=self.current_mutation_rate,
                exploration_level=self.current_exploration_level,
                rng=self.rng
            )

            new_population.append(child1)
            if len(new_population) < pop_size:
                new_population.append(child2)

        self.population = new_population

        # 8. Record Metric
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
            constraint_penalty=current_best_eval.constraint_penalty
        )
        self.history.append(metric)
        return metric

    def run(
        self,
        generations: int,
        callback: Optional[Callable[[GenerationMetric], None]] = None
    ) -> List[GenerationMetric]:
        """
        Runs optimization for a given number of generations.
        """
        new_metrics = []
        for _ in range(generations):
            m = self.step()
            new_metrics.append(m)
            if callback:
                callback(m)
        return new_metrics
