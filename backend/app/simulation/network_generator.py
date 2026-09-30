"""
Synthetic road network generator for AdaptIQ-R.
Generates reproducible, connected spatial road networks with nodes,
edges, distances, base travel times, traffic factors, and block states.
"""

import math
import random
from typing import Dict, List, Tuple, Set
import networkx as nx

from backend.app.core.models import (
    NodeModel,
    EdgeModel,
    NetworkScenarioModel,
    NodeType
)


def generate_synthetic_network(
    node_count: int = 20,
    seed: int = 42,
    grid_size: float = 100.0,
    k_neighbors: int = 4,
    priority_ratio: float = 0.20
) -> NetworkScenarioModel:
    """
    Generates a reproducible planar-like synthetic road network.
    Guarantees connectivity via Minimum Spanning Tree (MST) + k-nearest neighbor edges.
    """
    if node_count not in [10, 20, 50, 100]:
        # Support arbitrary sizes too, but ensure valid minimum
        if node_count < 4:
            raise ValueError(f"Scenario size {node_count} is too small. Minimum is 4 nodes.")

    rng = random.Random(seed)
    nodes: Dict[int, NodeModel] = {}

    # Node 0 is always the central Depot
    nodes[0] = NodeModel(
        id=0,
        x=round(grid_size / 2.0, 2),
        y=round(grid_size / 2.0, 2),
        type="depot",
        priority=0,
        demand=0.0
    )

    # Generate customer nodes uniformly in the 2D bounding area
    # Keep some minimum separation between nodes for clarity
    num_priority = max(1, int(round((node_count - 1) * priority_ratio)))
    priority_indices = set(rng.sample(range(1, node_count), num_priority))

    for i in range(1, node_count):
        x = round(rng.uniform(5.0, grid_size - 5.0), 2)
        y = round(rng.uniform(5.0, grid_size - 5.0), 2)
        node_type: NodeType = "priority" if i in priority_indices else "customer"
        priority_val = 3 if node_type == "priority" else 1
        demand_val = round(rng.uniform(1.0, 5.0), 1)

        nodes[i] = NodeModel(
            id=i,
            x=x,
            y=y,
            type=node_type,
            priority=priority_val,
            demand=demand_val
        )

    # Calculate all pairwise distances
    all_pairs: List[Tuple[float, int, int]] = []
    for u in range(node_count):
        for v in range(u + 1, node_count):
            dx = nodes[u].x - nodes[v].x
            dy = nodes[u].y - nodes[v].y
            dist = math.hypot(dx, dy)
            all_pairs.append((dist, u, v))

    all_pairs.sort(key=lambda item: item[0])

    # 1. Guarantee global connectivity via Kruskal's MST
    parent = list(range(node_count))

    def find(i: int) -> int:
        path = []
        while parent[i] != i:
            path.append(i)
            i = parent[i]
        for node in path:
            parent[node] = i
        return i

    def union(i: int, j: int) -> bool:
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False

    edge_set: Set[Tuple[int, int]] = set()
    for dist, u, v in all_pairs:
        if union(u, v):
            edge_set.add((min(u, v), max(u, v)))

    # 2. Add k-nearest neighbor edges to provide realistic route choices & redundancy
    k_val = min(k_neighbors, node_count - 1)
    for u in range(node_count):
        # find closest neighbors of u
        neighbors = []
        for v in range(node_count):
            if u != v:
                d = math.hypot(nodes[u].x - nodes[v].x, nodes[u].y - nodes[v].y)
                neighbors.append((d, v))
        neighbors.sort(key=lambda x: x[0])
        for d, v in neighbors[:k_val]:
            edge_set.add((min(u, v), max(u, v)))

    # Build EdgeModel list
    # Average speed: 40 km/h -> travel time = distance / 40.0 * 60.0 (minutes)
    edges: List[EdgeModel] = []
    for u, v in sorted(edge_set):
        dist = round(math.hypot(nodes[u].x - nodes[v].x, nodes[u].y - nodes[v].y), 2)
        base_time = round((dist / 40.0) * 60.0, 2)
        edges.append(EdgeModel(
            source=u,
            target=v,
            distance=dist,
            travel_time=base_time,
            traffic_factor=1.0,
            blocked=False
        ))

    scenario_id = f"scenario_{node_count}n_seed{seed}"
    return NetworkScenarioModel(
        id=scenario_id,
        seed=seed,
        node_count=node_count,
        depot_id=0,
        nodes=nodes,
        edges=edges
    )


def create_networkx_graph(scenario: NetworkScenarioModel) -> nx.Graph:
    """
    Converts a NetworkScenarioModel to a NetworkX Graph.
    Respects blocked status and dynamic traffic factors.
    """
    g = nx.Graph()
    for node_id, node in scenario.nodes.items():
        g.add_node(node_id, x=node.x, y=node.y, type=node.type, priority=node.priority)

    for edge in scenario.edges:
        effective_time = edge.travel_time * edge.traffic_factor
        g.add_edge(
            edge.source,
            edge.target,
            distance=edge.distance,
            base_time=edge.travel_time,
            effective_time=effective_time,
            traffic_factor=edge.traffic_factor,
            blocked=edge.blocked
        )
    return g
