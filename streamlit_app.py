import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import os
import sys

# Ensure backend package is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.simulation.network_generator import NetworkGenerator
from backend.app.simulation.disruption_engine import DisruptionEngine
from backend.app.optimizer.genetic_algorithm import GeneticAlgorithmOptimizer
from backend.app.fuzzy.fuzzy_controller import FuzzyController
from backend.app.evaluation.benchmark import run_single_comparison, run_benchmark_suite
from backend.app.core.models import DisruptionType

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
    gen = NetworkGenerator()
    st.session_state.scenario = gen.generate(node_count=20, seed=42)
if "optimizer" not in st.session_state:
    st.session_state.optimizer = None
if "opt_history" not in st.session_state:
    st.session_state.opt_history = []
if "disruption_engine" not in st.session_state:
    st.session_state.disruption_engine = DisruptionEngine()

def plot_network(scenario, route=None, blocked_edges=None):
    fig = go.Figure()
    coords = {n.id: (n.x, n.y) for n in scenario.nodes}
    
    # Plot normal edges
    for e in scenario.edges:
        if e.is_blocked:
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
        if e.is_blocked:
            x0, y0 = coords[e.source]
            x1, y1 = coords[e.target]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode="lines",
                line=dict(color="#ef4444", width=4, dash="dot"),
                name="Blocked Edge",
                hovertext=f"BLOCKED: {e.source}→{e.target}",
                showlegend=True
            ))

    # Plot customer nodes
    cust_x = [n.x for n in scenario.nodes if n.id != scenario.depot_id]
    cust_y = [n.y for n in scenario.nodes if n.id != scenario.depot_id]
    cust_ids = [n.id for n in scenario.nodes if n.id != scenario.depot_id]
    fig.add_trace(go.Scatter(
        x=cust_x, y=cust_y,
        mode="markers+text",
        marker=dict(size=14, color="#06b6d4", line=dict(color="#ffffff", width=1)),
        text=cust_ids,
        textposition="top center",
        name="Customers",
        hoverinfo="text"
    ))

    # Plot depot
    depot = next(n for n in scenario.nodes if n.id == scenario.depot_id)
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
            gen = NetworkGenerator()
            st.session_state.scenario = gen.generate(node_count=n_count, seed=int(seed))
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
            opt = GeneticAlgorithmOptimizer(
                scenario=st.session_state.scenario,
                is_adaptive=is_adapt,
                generations=gens,
                pop_size=pop_s,
                seed=st.session_state.scenario.seed
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
        if st.session_state.optimizer:
            best_ind = st.session_state.optimizer.best_individual
            st.plotly_chart(plot_network(st.session_state.scenario, route=best_ind.route), use_container_width=True)
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Best Fitness", f"{best_ind.fitness:.4f}")
            m2.metric("Total Distance", f"{best_ind.distance:.1f} km")
            m3.metric("Feasible", "Yes" if best_ind.is_feasible else "No")
            
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
                edge = st.session_state.disruption_engine.block_edge(st.session_state.scenario, s_node, t_node)
                if edge:
                    if st.session_state.optimizer:
                        st.session_state.optimizer.notify_disruption(st.session_state.scenario)
                    st.error(f"Severed edge {s_node} ↔ {t_node}!")
                else:
                    st.warning("Edge not found in network.")
                    
        elif d_type == "Traffic Surge":
            factor = st.slider("Traffic Congestion Multiplier", 1.5, 5.0, 3.0, 0.5)
            if st.button("Apply Traffic Surge"):
                st.session_state.disruption_engine.apply_traffic_surge(st.session_state.scenario, factor=factor)
                if st.session_state.optimizer:
                    st.session_state.optimizer.notify_disruption(st.session_state.scenario)
                st.warning(f"Surged traffic by {factor}x!")

        if st.session_state.optimizer and st.button("Recover & Adapt (30 Gens)", type="primary"):
            for _ in range(30):
                st.session_state.optimizer.step()
            st.success("Adaptive recovery cycle completed!")

    with col2:
        route = st.session_state.optimizer.best_individual.route if st.session_state.optimizer else None
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
