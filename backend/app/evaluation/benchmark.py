"""
Benchmark Engine for AdaptIQ-R.
Conducts head-to-head empirical evaluations between Baseline GA (fixed mutation rate)
and AdaptIQ-R (fuzzy-adaptive parameter control) across identical seeds and disruptions.
"""

import copy
import time
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from backend.app.core.models import (
    NetworkScenarioModel,
    OptimizationConfig,
    GenerationMetric
)
from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer


class BenchmarkResultSingle(BaseModel):
    seed: int
    algorithm: str  # "Baseline-GA" or "AdaptIQ-R"
    initial_best_fitness: float
    disrupted_fitness: float
    recovered_fitness: float
    recovery_generations: int
    recovery_time_sec: float
    total_runtime_sec: float
    is_feasible: bool
    final_diversity: float
    final_mutation_rate: float
    final_exploration_level: float


class BenchmarkSummary(BaseModel):
    node_count: int
    seeds_evaluated: List[int]
    baseline_mean_recovered_fitness: float
    adaptiq_mean_recovered_fitness: float
    baseline_std_fitness: float
    adaptiq_std_fitness: float
    baseline_mean_recovery_gens: float
    adaptiq_mean_recovery_gens: float
    baseline_mean_runtime_sec: float
    adaptiq_mean_runtime_sec: float
    adaptiq_fitness_improvement_pct: float
    runs: List[BenchmarkResultSingle] = Field(default_factory=list)


def run_single_comparison(
    node_count: int = 20,
    seed: int = 42,
    initial_gens: int = 60,
    recovery_gens: int = 60,
    pop_size: int = 80
) -> Dict[str, BenchmarkResultSingle]:
    """
    Runs an identical scenario and disruption for both Baseline GA and AdaptIQ-R.
    """
    # 1. Generate Scenario
    scenario_base = generate_synthetic_network(node_count=node_count, seed=seed)
    scenario_adapt = copy.deepcopy(scenario_base)

    # 2. Run Initial Optimization on Baseline GA (is_adaptive = False)
    cfg_base = OptimizationConfig(
        seed=seed,
        population_size=pop_size,
        generations=initial_gens,
        is_adaptive=False,
        initial_mutation_rate=0.15
    )
    opt_base = GeneticAlgorithmOptimizer(scenario=scenario_base, config=cfg_base)
    t0_base = time.perf_counter()
    opt_base.run(initial_gens)
    init_fit_base = opt_base.best_fitness

    # 3. Run Initial Optimization on AdaptIQ-R (is_adaptive = True)
    cfg_adapt = OptimizationConfig(
        seed=seed,
        population_size=pop_size,
        generations=initial_gens,
        is_adaptive=True,
        initial_mutation_rate=0.15
    )
    opt_adapt = GeneticAlgorithmOptimizer(scenario=scenario_adapt, config=cfg_adapt)
    t0_adapt = time.perf_counter()
    opt_adapt.run(initial_gens)
    init_fit_adapt = opt_adapt.best_fitness

    # 4. Determine a critical edge from the best route to disrupt
    best_edges = opt_adapt.best_evaluation.traversed_edges if opt_adapt.best_evaluation else []
    disrupt_edge = best_edges[len(best_edges) // 2] if best_edges else (1, 2)

    # 5. Inject identical Road Block into both scenarios
    engine_base = DisruptionEngine(scenario_base)
    engine_adapt = DisruptionEngine(scenario_adapt)

    engine_base.block_road(disrupt_edge[0], disrupt_edge[1])
    engine_adapt.block_road(disrupt_edge[0], disrupt_edge[1])

    opt_base.disruption_engine = engine_base
    opt_adapt.disruption_engine = engine_adapt
    opt_base.notify_disruption()
    opt_adapt.notify_disruption()

    # Disrupted evaluation
    disrupted_eval_base = opt_base.best_evaluation
    disrupted_eval_adapt = opt_adapt.best_evaluation
    disrupted_fit_base = disrupted_eval_base.fitness
    disrupted_fit_adapt = disrupted_eval_adapt.fitness

    # 6. Continue Optimization (Recovery Phase)
    # Baseline
    t_rec_base_start = time.perf_counter()
    rec_metrics_base = opt_base.run(recovery_gens)
    t_rec_base = time.perf_counter() - t_rec_base_start
    total_time_base = time.perf_counter() - t0_base

    # Find when baseline recovered to a feasible or plateaued solution
    base_rec_gens = recovery_gens
    for idx, m in enumerate(rec_metrics_base):
        if m.is_feasible and m.best_fitness <= opt_base.best_fitness * 1.05:
            base_rec_gens = idx + 1
            break

    # AdaptIQ-R
    t_rec_adapt_start = time.perf_counter()
    rec_metrics_adapt = opt_adapt.run(recovery_gens)
    t_rec_adapt = time.perf_counter() - t_rec_adapt_start
    total_time_adapt = time.perf_counter() - t0_adapt

    adapt_rec_gens = recovery_gens
    for idx, m in enumerate(rec_metrics_adapt):
        if m.is_feasible and m.best_fitness <= opt_adapt.best_fitness * 1.05:
            adapt_rec_gens = idx + 1
            break

    res_base = BenchmarkResultSingle(
        seed=seed,
        algorithm="Baseline-GA",
        initial_best_fitness=init_fit_base,
        disrupted_fitness=disrupted_fit_base,
        recovered_fitness=opt_base.best_fitness,
        recovery_generations=base_rec_gens,
        recovery_time_sec=round(t_rec_base, 3),
        total_runtime_sec=round(total_time_base, 3),
        is_feasible=opt_base.best_evaluation.is_feasible if opt_base.best_evaluation else False,
        final_diversity=opt_base.current_diversity,
        final_mutation_rate=opt_base.current_mutation_rate,
        final_exploration_level=opt_base.current_exploration_level
    )

    res_adapt = BenchmarkResultSingle(
        seed=seed,
        algorithm="AdaptIQ-R",
        initial_best_fitness=init_fit_adapt,
        disrupted_fitness=disrupted_fit_adapt,
        recovered_fitness=opt_adapt.best_fitness,
        recovery_generations=adapt_rec_gens,
        recovery_time_sec=round(t_rec_adapt, 3),
        total_runtime_sec=round(total_time_adapt, 3),
        is_feasible=opt_adapt.best_evaluation.is_feasible if opt_adapt.best_evaluation else False,
        final_diversity=opt_adapt.current_diversity,
        final_mutation_rate=opt_adapt.current_mutation_rate,
        final_exploration_level=opt_adapt.current_exploration_level
    )

    return {"baseline": res_base, "adaptiq": res_adapt}


def run_benchmark_suite(
    node_count: int = 20,
    seeds: Optional[List[int]] = None,
    initial_gens: int = 50,
    recovery_gens: int = 50,
    pop_size: int = 60
) -> BenchmarkSummary:
    """
    Executes benchmark across multiple seeds and aggregates statistical metrics.
    """
    if seeds is None:
        seeds = [42, 123, 456, 789, 1011]

    runs: List[BenchmarkResultSingle] = []
    base_fits = []
    adapt_fits = []
    base_gens = []
    adapt_gens = []
    base_times = []
    adapt_times = []

    for s in seeds:
        pair = run_single_comparison(
            node_count=node_count,
            seed=s,
            initial_gens=initial_gens,
            recovery_gens=recovery_gens,
            pop_size=pop_size
        )
        b = pair["baseline"]
        a = pair["adaptiq"]
        runs.extend([b, a])

        base_fits.append(b.recovered_fitness)
        adapt_fits.append(a.recovered_fitness)
        base_gens.append(b.recovery_generations)
        adapt_gens.append(a.recovery_generations)
        base_times.append(b.recovery_time_sec)
        adapt_times.append(a.recovery_time_sec)

    mean_b_fit = float(np.mean(base_fits))
    mean_a_fit = float(np.mean(adapt_fits))
    std_b_fit = float(np.std(base_fits))
    std_a_fit = float(np.std(adapt_fits))

    mean_b_gens = float(np.mean(base_gens))
    mean_a_gens = float(np.mean(adapt_gens))
    mean_b_time = float(np.mean(base_times))
    mean_a_time = float(np.mean(adapt_times))

    # Positive percentage = improvement (lower fitness is better)
    pct_imp = round(((mean_b_fit - mean_a_fit) / max(1e-9, mean_b_fit)) * 100.0, 2)

    return BenchmarkSummary(
        node_count=node_count,
        seeds_evaluated=seeds,
        baseline_mean_recovered_fitness=round(mean_b_fit, 4),
        adaptiq_mean_recovered_fitness=round(mean_a_fit, 4),
        baseline_std_fitness=round(std_b_fit, 4),
        adaptiq_std_fitness=round(std_a_fit, 4),
        baseline_mean_recovery_gens=round(mean_b_gens, 2),
        adaptiq_mean_recovery_gens=round(mean_a_gens, 2),
        baseline_mean_runtime_sec=round(mean_b_time, 3),
        adaptiq_mean_runtime_sec=round(mean_a_time, 3),
        adaptiq_fitness_improvement_pct=pct_imp,
        runs=runs
    )
