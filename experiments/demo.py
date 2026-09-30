"""
AdaptIQ-R Demonstration Script.
Fulfills First Milestone requirement:
1. Generates 20-node synthetic road network with seed 42.
2. Runs baseline GA and AdaptIQ-R initial optimization.
3. Identifies an actively traversed edge from the best route and blocks it.
4. Calculates quantitative disruption severity.
5. Queries Mamdani fuzzy controller, demonstrating adaptive mutation and exploration changes.
6. Executes adaptive recovery optimization to find an alternative feasible route.
7. Prints clean research diagnostics and exports results to experiments/results/.
"""

import copy
import json
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.core.models import OptimizationConfig


def run_demo():
    print("=" * 50)
    print("ADAPTIQ-R DEMO")
    print("Adaptive Route Optimization Under Disruption")
    print("=" * 50)

    node_count = 20
    seed = 42
    initial_generations = 50
    recovery_generations = 50
    pop_size = 100

    print("\nScenario")
    print(f"Nodes: {node_count}")
    print(f"Seed: {seed}")

    # 1. Generate Scenario
    scenario = generate_synthetic_network(node_count=node_count, seed=seed)
    print(f"Generated network with {len(scenario.nodes)} nodes and {len(scenario.edges)} edges (guaranteed connected).")

    # 2. Run Baseline GA for comparative baseline
    print("\nRunning Baseline GA (Fixed mutation rate = 0.15)...")
    baseline_cfg = OptimizationConfig(
        seed=seed,
        population_size=pop_size,
        generations=initial_generations,
        is_adaptive=False,
        initial_mutation_rate=0.15
    )
    opt_baseline = GeneticAlgorithmOptimizer(scenario=copy.deepcopy(scenario), config=baseline_cfg)
    opt_baseline.run(initial_generations)
    baseline_initial_fit = opt_baseline.best_fitness

    # 3. Run AdaptIQ-R Initial Optimization
    print("\nRunning AdaptIQ-R Initial Optimization (Fuzzy-Adaptive)...")
    adapt_cfg = OptimizationConfig(
        seed=seed,
        population_size=pop_size,
        generations=initial_generations,
        is_adaptive=True,
        initial_mutation_rate=0.15
    )
    disruption_engine = DisruptionEngine(scenario)
    opt_adaptiq = GeneticAlgorithmOptimizer(
        scenario=scenario,
        config=adapt_cfg,
        disruption_engine=disruption_engine
    )

    for g in range(initial_generations):
        metric = opt_adaptiq.step()
        if (g + 1) % 10 == 0 or g == 0:
            print(f"  Gen {metric.generation:02d} | Best Fit: {metric.best_fitness:.4f} | Div: {metric.population_diversity:.3f} | Mut: {metric.mutation_rate:.3f} | Exp: {metric.exploration_level:.3f}")

    init_best_eval = opt_adaptiq.best_evaluation
    init_fitness = init_best_eval.fitness
    init_route = list(init_best_eval.node_sequence)

    print("\nINITIAL OPTIMIZATION")
    print(f"Best Fitness: {init_fitness:.4f}")
    print(f"Distance: {init_best_eval.total_distance:.2f} km | Travel Time: {init_best_eval.total_travel_time:.2f} min")
    print(f"Route: {init_route}")

    # 4. Inject Road Block on an actively traversed road
    traversed = init_best_eval.traversed_edges
    if traversed:
        # Choose a critical central edge
        block_u, block_v = traversed[len(traversed) // 2]
    else:
        block_u, block_v = scenario.edges[0].source, scenario.edges[0].target

    print("\nDISRUPTION")
    print("Type: ROAD BLOCK")
    print(f"Edge: {block_u} -> {block_v} BLOCKED")

    mut_before = opt_adaptiq.current_mutation_rate
    exp_before = opt_adaptiq.current_exploration_level

    # Apply the road block
    disruption_engine.block_road(block_u, block_v)
    opt_adaptiq.notify_disruption()

    # Recalculate severity and disrupted fitness
    severity_obj = disruption_engine.calculate_severity()
    disrupted_eval = opt_adaptiq.best_evaluation
    disrupted_fitness = disrupted_eval.fitness

    print(f"Severity: {severity_obj.severity:.4f} (Blocked edge ratio: {severity_obj.blocked_edge_ratio:.4f})")
    print(f"Disrupted Route Fitness: {disrupted_fitness:.4f} (Degraded from {init_fitness:.4f})")

    # 5. Fuzzy Controller Response
    # In next step, fuzzy controller reads degraded improvement and high disruption severity
    opt_adaptiq.step()  # Generation 51
    mut_after = opt_adaptiq.current_mutation_rate
    exp_after = opt_adaptiq.current_exploration_level

    print("\nFUZZY CONTROLLER")
    print(f"Diversity: {opt_adaptiq.current_diversity:.4f}")
    print(f"Improvement: {opt_adaptiq.current_improvement:.4f}")
    print(f"Disruption: {opt_adaptiq.current_severity:.4f}")
    print("\nActivated Rules:")
    for r in opt_adaptiq.activated_rules:
        print(f"  {r}")

    print("\nMutation Rate:")
    print(f"  Before: {mut_before:.4f}")
    print(f"  After:  {mut_after:.4f}")

    print("\nExploration Level:")
    print(f"  Before: {exp_before:.4f}")
    print(f"  After:  {exp_after:.4f}")

    # 6. Adaptive Recovery Optimization
    print("\nRECOVERY PHASE")
    print("Searching for alternative feasible route avoiding blocked road...")
    t_start = time.perf_counter()
    recovery_metrics = []

    for g in range(recovery_generations - 1):
        m = opt_adaptiq.step()
        recovery_metrics.append(m)
        if (g + 1) % 10 == 0:
            print(f"  Gen {m.generation:02d} | Best Fit: {m.best_fitness:.4f} | Mut: {m.mutation_rate:.3f} | Exp: {m.exploration_level:.3f} | Feasible: {m.is_feasible}")

    rec_time = time.perf_counter() - t_start
    recovered_eval = opt_adaptiq.best_evaluation
    recovered_fit = recovered_eval.fitness
    recovered_route = recovered_eval.node_sequence

    # Calculate generation where feasible recovered route was re-established
    rec_gens = recovery_generations
    for idx, m in enumerate(recovery_metrics):
        if m.is_feasible and m.best_fitness <= recovered_fit * 1.05:
            rec_gens = idx + 1
            break

    print("\nRECOVERY")
    print(f"Recovered Fitness: {recovered_fit:.4f}")
    print(f"Recovery Generations: {rec_gens}")
    print(f"Recovery Time: {rec_time:.3f} s")
    print(f"Distance: {recovered_eval.total_distance:.2f} km | Travel Time: {recovered_eval.total_travel_time:.2f} min")
    print(f"Recovered Route: {recovered_route}")
    print(f"Is Feasible: {recovered_eval.is_feasible}")
    has_blocked_edge = (min(block_u, block_v), max(block_u, block_v)) in recovered_eval.traversed_edges
    print(f"Traverses Blocked Edge ({block_u}, {block_v}): {has_blocked_edge} (Should be False)")

    # 7. Save JSON Record
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(results_dir, f"demo_20nodes_seed{seed}_{timestamp_str}.json")

    demo_data = {
        "scenario": {
            "node_count": node_count,
            "seed": seed,
            "edge_count": len(scenario.edges)
        },
        "baseline_initial_fitness": baseline_initial_fit,
        "initial_optimization": {
            "best_fitness": init_fitness,
            "route": init_route,
            "distance": init_best_eval.total_distance,
            "travel_time": init_best_eval.total_travel_time
        },
        "disruption": {
            "type": "road_block",
            "edge": [block_u, block_v],
            "severity": severity_obj.severity,
            "disrupted_fitness": disrupted_fitness
        },
        "fuzzy_response": {
            "diversity": opt_adaptiq.current_diversity,
            "improvement": opt_adaptiq.current_improvement,
            "disruption_severity": opt_adaptiq.current_severity,
            "activated_rules": opt_adaptiq.activated_rules,
            "mutation_before": mut_before,
            "mutation_after": mut_after,
            "exploration_before": exp_before,
            "exploration_after": exp_after
        },
        "recovery": {
            "recovered_fitness": recovered_fit,
            "recovery_generations": rec_gens,
            "recovery_time_sec": round(rec_time, 3),
            "recovered_route": recovered_route,
            "is_feasible": recovered_eval.is_feasible,
            "traversed_blocked_edge": has_blocked_edge
        },
        "history": [m.model_dump() for m in opt_adaptiq.history]
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(demo_data, f, indent=2)

    print("\nRESULTS SAVED")
    print(f"{filepath}")
    print("=" * 50)
    return demo_data


if __name__ == "__main__":
    run_demo()
