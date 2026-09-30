"""
Benchmarking API routes.
Runs empirical head-to-head comparisons across multiple seeds.
"""

import threading
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.evaluation.benchmark import run_benchmark_suite, BenchmarkSummary

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark"])

# Benchmark results storage
BENCHMARKS: Dict[str, Dict] = {}


class RunBenchmarkRequest(BaseModel):
    node_count: int = Field(default=20, description="10, 20, 50, 100")
    seeds: Optional[List[int]] = Field(default=None, description="List of integer seeds")
    initial_gens: int = Field(default=40, ge=10, le=200)
    recovery_gens: int = Field(default=40, ge=10, le=200)
    pop_size: int = Field(default=60, ge=20, le=200)


def _benchmark_worker(benchmark_id: str, req: RunBenchmarkRequest):
    try:
        summary = run_benchmark_suite(
            node_count=req.node_count,
            seeds=req.seeds,
            initial_gens=req.initial_gens,
            recovery_gens=req.recovery_gens,
            pop_size=req.pop_size
        )
        BENCHMARKS[benchmark_id] = {
            "id": benchmark_id,
            "status": "completed",
            "summary": summary.model_dump()
        }
    except Exception as e:
        BENCHMARKS[benchmark_id] = {
            "id": benchmark_id,
            "status": "failed",
            "error": str(e)
        }


@router.post("/run")
def run_benchmark(req: RunBenchmarkRequest):
    benchmark_id = f"bench_{uuid.uuid4().hex[:8]}"
    BENCHMARKS[benchmark_id] = {
        "id": benchmark_id,
        "status": "running",
        "summary": None
    }

    t = threading.Thread(target=_benchmark_worker, args=(benchmark_id, req), daemon=True)
    t.start()

    return {"benchmark_id": benchmark_id, "status": "running"}


@router.get("/{benchmark_id}")
def get_benchmark(benchmark_id: str):
    if benchmark_id not in BENCHMARKS:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return BENCHMARKS[benchmark_id]
