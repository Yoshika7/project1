"""
Experiment management and JSON artifact serialization for AdaptIQ-R.
Logs full research telemetry including per-generation metrics and fuzzy decisions.
"""

import json
import os
import time
from typing import Dict, Any, Optional

from backend.app.core.models import (
    NetworkScenarioModel,
    OptimizationConfig,
    GenerationMetric,
    DisruptionEvent
)


def export_experiment_log(
    scenario: NetworkScenarioModel,
    config: OptimizationConfig,
    history: list,
    disruptions: list,
    output_dir: str = "experiments/results",
    prefix: str = "run"
) -> str:
    """
    Serializes a complete optimization run to a timestamped JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    algo_name = "AdaptIQ-R" if config.is_adaptive else "Baseline-GA"
    filename = f"{prefix}_{algo_name}_seed{config.seed}_{timestamp_str}.json"
    filepath = os.path.join(output_dir, filename)

    data = {
        "timestamp": timestamp_str,
        "algorithm": algo_name,
        "config": config.model_dump(),
        "scenario": {
            "id": scenario.id,
            "seed": scenario.seed,
            "node_count": scenario.node_count,
            "depot_id": scenario.depot_id,
            "edge_count": len(scenario.edges)
        },
        "disruptions": [
            d.model_dump() if hasattr(d, "model_dump") else d for d in disruptions
        ],
        "final_metrics": history[-1].model_dump() if history else None,
        "history": [
            m.model_dump() if hasattr(m, "model_dump") else m for m in history
        ]
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filepath
