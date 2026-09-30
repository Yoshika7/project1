import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.simulation.network_generator import generate_synthetic_network
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.core.models import OptimizationConfig
from backend.app.evaluation.benchmark import run_single_comparison, run_benchmark_suite

st.set_page_config(
    page_title="AdaptIQ-R | Adaptive Route Optimization",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark CI research theme
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric { background-color: #111827; padding: 12px; border-radius: 8px; border: 1px solid #1f2937; }
    h1, h2, h3 { color: #f9fafb !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ AdaptIQ-R: Adaptive Route Optimization Under Disruption")
st.caption("Computational Intelligence Research: Evolutionary Algorithm + Online Mamdani Fuzzy Controller")

# Sidebar navigation
st.sidebar.header("Navigation & Settings")
page = st.sidebar.radio("Go to view:", [
    "🌐 Scenario & Network",
    "🚀 Run Optimizer",
    "🚨 Disruption Lab",
    "⚔️ Head-to-Head Comparison",
    "📊 Benchmark Suite"
])

# Session state initialization
if "scenario" not in st.session_state:
    st.session_state.scenario = generate_synthetic_network(node_count=20, seed=42)
if "disruption_engine" not in st.session_state:
    st.session_state.disruption_engine = DisruptionEngine(st.session_state.scenario)
if "optimizer" not in st.session_state:
    st.session_state.optimizer = None
if "opt_history" not in st.session_state:
    st.session_state.opt_history = []

def plot_network(scenario, route=None):
    fig = go.Figure()
    coords = {nid: (node.x, node.y) for nid, node in scenario.nodes.items()}
    
    # Plot normal edges
    for e in scenario.edges:
        if e.blocked:
            continue
        x0, y0 = coords[e.source]
        x1, y1 = coords[e.target]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color="#334155", width=1.5),
            hoverinfo="none",
            showlegend=False
        ))
        
    # Plot blocked edges in bright red
    for e in scenario.edges:
        if e.blocked:
            x0, y0 = coords[e.source]
            x1, y1 = coords[e.target]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode="lines",
                line=dict(color="#ef4444", width=4, dash="dot"),
                name=f"Blocked: {e.source}↔{e.target}",
                hovertext=f"BLOCKED: {e.source}↔{e.target}",
                showlegend=True
            ))

    # Plot customer nodes
    cust_nodes = [node for nid, node in scenario.nodes.items() if nid != scenario.depot_id]
    fig.add_trace(go.Scatter(
        x=[n.x for n in cust_nodes],
        y=[n.y for n in cust_nodes],
        mode="markers+text",
        marker=dict(size=14, color="#06b6d4", line=dict(color="#ffffff", width=1)),
        text=[n.id for n in cust_nodes],
        textposition="top center",
        name="Customers",
        hoverinfo="text"
    ))

    # Plot depot
    depot = scenario.nodes[scenario.depot_id]
    fig.add_trace(go.Scatter(
        x=[depot.x], y=[depot.y],
        mode="markers+text",
        marker=dict(size=20, color="#f59e0b", symbol="star"),
        text=["DEPOT (0)"],
        textposition="bottom center",
        name="Depot",
        hoverinfo="text"
    ))

    # Plot Route if present
    if route and len(route) > 1:
        full_route = [scenario.depot_id] + list(route) + [scenario.depot_id]
        rx, ry = [], []
        for nid in full_route:
            rx.append(coords[nid][0])
            ry.append(coords[nid][1])
        fig.add_trace(go.Scatter(
            x=rx, y=ry,
            mode="lines+markers",
            line=dict(color="#10b981", width=3),
            marker=dict(size=6, color="#10b981"),
            name="Active Route"
        ))

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    return fig

# ----------------- VIEW 1: SCENARIO -----------------
if page == "🌐 Scenario & Network":
    st.subheader("Synthetic Network Generator")
    col1, col2 = st.columns([1, 3])
    with col1:
        n_count = st.selectbox("Node Count", [10, 20, 50], index=1)
        seed = st.number_input("Random Seed", value=42, step=1)
        if st.button("Generate Network", use_container_width=True):
            st.session_state.scenario = generate_synthetic_network(node_count=n_count, seed=int(seed))
            st.session_state.disruption_engine = DisruptionEngine(st.session_state.scenario)
            st.session_state.optimizer = None
            st.session_state.opt_history = []
            st.success(f"Generated {n_count}-node network (Seed {seed})")

        st.metric("Total Nodes", st.session_state.scenario.node_count)
        st.metric("Total Edges", len(st.session_state.scenario.edges))
        st.metric("Depot Node", st.session_state.scenario.depot_id)

    with col2:
        st.plotly_chart(plot_network(st.session_state.scenario), use_container_width=True)

# ----------------- VIEW 2: OPTIMIZER -----------------
elif page == "🚀 Run Optimizer":
    st.subheader("Genetic Algorithm Optimization")
    col1, col2 = st.columns([1, 2])
    with col1:
        is_adapt = st.radio("Optimization Mode", ["AdaptIQ-R (Fuzzy Adaptive)", "Baseline GA (Static 0.15)"]) == "AdaptIQ-R (Fuzzy Adaptive)"
        gens = st.slider("Generations", min_value=20, max_value=150, value=50, step=10)
        pop_s = st.slider("Population Size", min_value=20, max_value=100, value=60, step=10)

        if st.button("Start Optimization", type="primary", use_container_width=True):
            cfg = OptimizationConfig(
                is_adaptive=is_adapt,
                generations=gens,
                population_size=pop_s,
                seed=st.session_state.scenario.seed
            )
            opt = GeneticAlgorithmOptimizer(
                scenario=st.session_state.scenario,
                config=cfg,
                disruption_engine=st.session_state.disruption_engine
            )
            prog_bar = st.progress(0)
            status_text = st.empty()
            
            for g in range(gens):
                m = opt.step()
                prog_bar.progress((g + 1) / gens)
                status_text.text(f"Generation {g+1}/{gens} - Best Fitness: {m.best_fitness:.4f}")
            
            st.session_state.optimizer = opt
            st.session_state.opt_history = opt.history
            st.success("Optimization finished!")

    with col2:
        if st.session_state.optimizer and st.session_state.optimizer.best_evaluation:
            best_eval = st.session_state.optimizer.best_evaluation
            st.plotly_chart(plot_network(st.session_state.scenario, route=best_eval.route), use_container_width=True)
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Best Fitness", f"{best_eval.fitness:.4f}")
            m2.metric("Total Distance", f"{best_eval.distance:.1f} km")
            m3.metric("Feasible", "Yes" if best_eval.is_feasible else "No")
            
            # History Chart
            df = pd.DataFrame([{
                "Generation": m.generation,
                "Best Fitness": m.best_fitness,
                "Avg Fitness": m.avg_fitness,
                "Diversity": m.population_diversity,
                "Mutation Rate": m.mutation_rate
            } for m in st.session_state.opt_history])
            
            st.line_chart(df.set_index("Generation")[["Best Fitness", "Avg Fitness"]])
            if is_adapt:
                st.line_chart(df.set_index("Generation")[["Diversity", "Mutation Rate"]])

# ----------------- VIEW 3: DISRUPTION -----------------
elif page == "🚨 Disruption Lab":
    st.subheader("Dynamic Disruption & Rerouting")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Inject Disruption")
        d_type = st.selectbox("Disruption Type", ["Road Block", "Traffic Surge", "Vehicle Failure"])
        
        if d_type == "Road Block":
            s_node = st.number_input("Source Node", min_value=0, max_value=len(st.session_state.scenario.nodes)-1, value=1)
            t_node = st.number_input("Target Node", min_value=0, max_value=len(st.session_state.scenario.nodes)-1, value=2)
            if st.button("Apply Road Block"):
                try:
                    sev = st.session_state.disruption_engine.block_road(int(s_node), int(t_node))
                    if st.session_state.optimizer:
                        st.session_state.optimizer.notify_disruption()
                    st.error(f"Severed edge {s_node} ↔ {t_node}! Severity: {sev.severity:.4f}")
                except Exception as ex:
                    st.warning(str(ex))
                    
        elif d_type == "Traffic Surge":
            factor = st.slider("Traffic Congestion Multiplier", 1.5, 5.0, 3.0, 0.5)
            if st.button("Apply Traffic Surge"):
                sev = st.session_state.disruption_engine.surge_traffic(edges=None, factor=factor)
                if st.session_state.optimizer:
                    st.session_state.optimizer.notify_disruption()
                st.warning(f"Surged traffic by {factor}x! Severity: {sev.severity:.4f}")

        elif d_type == "Vehicle Failure":
            loss = st.slider("Capacity Loss", 0.1, 0.8, 0.4, 0.1)
            if st.button("Simulate Vehicle Failure"):
                sev = st.session_state.disruption_engine.simulate_vehicle_failure(loss)
                if st.session_state.optimizer:
                    st.session_state.optimizer.notify_disruption()
                st.error(f"Vehicle capacity reduced by {int(loss*100)}%! Severity: {sev.severity:.4f}")

        if st.session_state.optimizer and st.button("Recover & Adapt (30 Gens)", type="primary"):
            for _ in range(30):
                st.session_state.optimizer.step()
            st.success("Adaptive recovery cycle completed!")

    with col2:
        route = st.session_state.optimizer.best_evaluation.route if (st.session_state.optimizer and st.session_state.optimizer.best_evaluation) else None
        st.plotly_chart(plot_network(st.session_state.scenario, route=route), use_container_width=True)

# ----------------- VIEW 4: COMPARISON -----------------
elif page == "⚔️ Head-to-Head Comparison":
    st.subheader("Direct Comparison: Baseline GA vs AdaptIQ-R")
    
    if st.button("Run Head-to-Head Test", type="primary"):
        with st.spinner("Executing comparative algorithms..."):
            res = run_single_comparison(
                scenario=st.session_state.scenario,
                initial_gens=40,
                recovery_gens=40,
                pop_size=60,
                seed=st.session_state.scenario.seed
            )
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline Final Fitness", f"{res['baseline_recovered_fitness']:.4f}")
        c2.metric("AdaptIQ-R Final Fitness", f"{res['adaptiq_recovered_fitness']:.4f}")
        diff = ((res['baseline_recovered_fitness'] - res['adaptiq_recovered_fitness']) / res['baseline_recovered_fitness']) * 100
        c3.metric("AdaptIQ-R Advantage", f"{diff:+.2f}%")
        
        comp_df = pd.DataFrame({
            "Baseline GA": [m.best_fitness for m in res['baseline_history']],
            "AdaptIQ-R": [m.best_fitness for m in res['adaptiq_history']]
        })
        st.line_chart(comp_df)

# ----------------- VIEW 5: BENCHMARK -----------------
elif page == "📊 Benchmark Suite":
    st.subheader("Multi-Seed Statistical Verification")
    seeds_input = st.text_input("Test Seeds (comma-separated)", "42, 123, 456")
    
    if st.button("Execute Benchmark Suite", type="primary"):
        parsed_seeds = [int(s.strip()) for s in seeds_input.split(",") if s.strip().isdigit()]
        with st.spinner(f"Benchmarking across {len(parsed_seeds)} seeds..."):
            summary = run_benchmark_suite(
                node_count=st.session_state.scenario.node_count,
                seeds=parsed_seeds,
                initial_gens=30,
                recovery_gens=30,
                pop_size=50
            )
            
        st.success("Benchmark completed successfully!")
        
        b1, b2 = st.columns(2)
        b1.metric("Baseline Mean Fitness", f"{summary.baseline_mean_recovered_fitness:.4f}")
        b2.metric("AdaptIQ-R Mean Fitness", f"{summary.adaptiq_mean_recovered_fitness:.4f}")
        st.metric("Average Improvement", f"{summary.adaptiq_fitness_improvement_pct:+.2f}%")
