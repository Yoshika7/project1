"""
Fitness Engine for AdaptIQ-R.
Evaluates candidate routes using Dijkstra pathfinding on the synthetic road network.
Combines normalized distance, travel time, and constraint penalties.
"""

import math
from typing import List, Tuple, Dict, Optional
import networkx as nx

from backend.app.core.models import (
    NetworkScenarioModel,
    RouteEvaluation,
    OptimizationConfig
)
from backend.app.core.config import (
    DEFAULT_DISTANCE_WEIGHT,
    DEFAULT_TIME_WEIGHT,
    DEFAULT_PENALTY_WEIGHT,
    PENALTY_UNREACHABLE_SEGMENT,
    PENALTY_BLOCKED_EDGE_USED
)
from backend.app.simulation.constraints import (
    evaluate_priority_penalty,
    evaluate_capacity_penalty
)


class FitnessEngine:
    """
    Evaluates candidate routes over a NetworkScenarioModel.
    Separates GA sequencing responsibilities from graph Dijkstra pathfinding.
    """

    def __init__(
        self,
        scenario: NetworkScenarioModel,
        distance_weight: float = DEFAULT_DISTANCE_WEIGHT,
        time_weight: float = DEFAULT_TIME_WEIGHT,
        penalty_weight: float = DEFAULT_PENALTY_WEIGHT
    ):
        self.scenario = scenario
        self.w_d = distance_weight
        self.w_t = time_weight
        self.w_p = penalty_weight

        # Precompute normalization scales based on scenario dimensions
        node_count = max(4, len(scenario.nodes))
        # Bounding box approximate diagonal
        xs = [n.x for n in scenario.nodes.values()]
        ys = [n.y for n in scenario.nodes.values()]
        diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) if xs and ys else 100.0
        self.dist_scale = max(10.0, node_count * (diag / 3.0))
        self.time_scale = max(10.0, (self.dist_scale / 40.0) * 60.0)
        self.penalty_scale = 100.0

        self._active_graph: Optional[nx.Graph] = None
        self._graph_dirty = True

    def invalidate_cache(self) -> None:
        """Call whenever scenario edges (traffic, blocked) change."""
        self._graph_dirty = True

    def get_navigable_graph(self) -> nx.Graph:
        """
        Returns graph containing only unblocked edges with dynamic weights.
        """
        if self._graph_dirty or self._active_graph is None:
            g = nx.Graph()
            for nid, node in self.scenario.nodes.items():
                g.add_node(nid, x=node.x, y=node.y, priority=node.priority)

            for edge in self.scenario.edges:
                if not edge.blocked:
                    eff_time = edge.travel_time * edge.traffic_factor
                    g.add_edge(
                        edge.source,
                        edge.target,
                        distance=edge.distance,
                        travel_time=eff_time,
                        weight=eff_time  # Primary traversal weight for Dijkstra
                    )
            self._active_graph = g
            self._graph_dirty = False
        return self._active_graph

    def evaluate_route(self, candidate: List[int]) -> RouteEvaluation:
        """
        Evaluates a candidate route sequence.
        If candidate does not start/end with depot (0), automatically surrounds with depot.
        Uses Dijkstra to route between consecutive sequence nodes.
        """
        if not candidate:
            return RouteEvaluation(
                node_sequence=[],
                total_distance=1e6,
                total_travel_time=1e6,
                constraint_penalty=1e6,
                fitness=1e6,
                is_feasible=False
            )

        # Standardize full sequence: Depot -> [Customers] -> Depot
        seq: List[int] = list(candidate)
        if seq[0] != self.scenario.depot_id:
            seq = [self.scenario.depot_id] + seq
        if seq[-1] != self.scenario.depot_id:
            seq = seq + [self.scenario.depot_id]

        g = self.get_navigable_graph()

        detailed_path: List[int] = [seq[0]]
        total_distance = 0.0
        total_time = 0.0
        penalty = 0.0
        is_feasible = True
        traversed_edges: List[Tuple[int, int]] = []
        unreachable_segments: List[Tuple[int, int]] = []

        # Dijkstra graph-level pathfinding between consecutive selected stops
        for i in range(len(seq) - 1):
            u, v = seq[i], seq[i + 1]
            if u == v:
                continue

            try:
                # Find shortest path on navigable (unblocked) graph
                path = nx.shortest_path(g, source=u, target=v, weight="weight")
                # Accumulate distance and time along Dijkstra path
                for step in range(len(path) - 1):
                    p_u, p_v = path[step], path[step + 1]
                    edge_data = g.get_edge_data(p_u, p_v)
                    total_distance += edge_data.get("distance", 0.0)
                    total_time += edge_data.get("travel_time", 0.0)
                    traversed_edges.append((min(p_u, p_v), max(p_u, p_v)))
                    if step > 0:
                        detailed_path.append(p_u)
                detailed_path.append(v)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # The segment is unreachable due to blocked roads or disconnectivity
                is_feasible = False
                unreachable_segments.append((u, v))
                penalty += PENALTY_UNREACHABLE_SEGMENT

                # Fallback Euclidean estimate so fitness remains computable
                n_u = self.scenario.nodes[u]
                n_v = self.scenario.nodes[v]
                fallback_dist = math.hypot(n_u.x - n_v.x, n_u.y - n_v.y)
                total_distance += fallback_dist * 2.0
                total_time += (fallback_dist / 20.0) * 60.0
                detailed_path.append(v)

        # Constraint: Priority ordering
        p_penalty = evaluate_priority_penalty(seq, self.scenario.nodes)
        penalty += p_penalty

        # Normalization
        d_norm = total_distance / self.dist_scale
        t_norm = total_time / self.time_scale
        p_norm = penalty / (penalty + self.penalty_scale) if penalty > 0 else 0.0

        fitness = round(self.w_d * d_norm + self.w_t * t_norm + self.w_p * p_norm, 4)

        return RouteEvaluation(
            node_sequence=seq,
            detailed_path=detailed_path,
            total_distance=round(total_distance, 2),
            total_travel_time=round(total_time, 2),
            constraint_penalty=round(penalty, 2),
            fitness=fitness,
            is_feasible=is_feasible,
            traversed_edges=traversed_edges,
            unreachable_segments=unreachable_segments
        )
