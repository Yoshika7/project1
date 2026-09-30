"""
FastAPI application entrypoint for AdaptIQ-R.
Exposes REST endpoints for scenario generation, evolutionary optimization,
disruption injection, and benchmarking.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_scenario import router as scenario_router
from backend.app.api.routes_optimization import router as optimization_router
from backend.app.api.routes_disruption import router as disruption_router
from backend.app.api.routes_benchmark import router as benchmark_router

app = FastAPI(
    title="AdaptIQ-R API",
    description="Adaptive Route Optimization Under Disruption — Computational Intelligence Research Engine",
    version="1.0.0"
)

# Enable CORS for local frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scenario_router)
app.include_router(optimization_router)
app.include_router(disruption_router)
app.include_router(benchmark_router)


@app.get("/")
def read_root():
    return {
        "project": "AdaptIQ-R",
        "description": "Adaptive Route Optimization Under Disruption",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
