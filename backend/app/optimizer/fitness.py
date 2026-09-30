"""
Fitness Engine for AdaptIQ-R.

Evaluates candidate routes by running Dijkstra shortest-path queries on a
dynamically maintained road-network graph.  The composite fitness objective is
a normalised weighted sum of distance, travel time, and constraint penalties.

Complexity Summary
------------------
- get_navigable_graph  : O(|V| + |E|) rebuild, O(1) cached hit
- evaluate_route       : O(k * (|V| log |V| + |E|)) — k = # consecutive stop pairs
- invalidate_cache     : O(1)

Where |V| = number of network nodes, |E| = number of edges.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import networkx as nx

from backend.app.core.models import (
    NetworkScenarioModel,
    OptimizationConfig,
    RouteEvaluation,
)
from backend.app.core.config import (
    DEFAULT_DISTANCE_WEIGHT,
    DEFAULT_PENALTY_WEIGHT,
    DEFAULT_TIME_WEIGHT,
    PENALTY_BLOCKED_EDGE_USED,
    PENALTY_UNREACHABLE_SEGMENT,
)
from backend.app.simulation.constraints import (
    evaluate_capacity_penalty,
    evaluate_priority_penalty,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["FitnessEngine"]


class FitnessEngine:
    """Evaluate candidate permutation routes over a :class:`NetworkScenarioModel`.

    Responsibilities
    ----------------
    * Maintain a *lazily rebuilt* ``networkx.Graph`` reflecting the current
      blocked/traffic state of the scenario edges.
    * Perform Dijkstra shortest-path routing between each consecutive pair of
      stops in a candidate permutation.
    * Aggregate distance, travel time, and constraint penalties into a single
      normalised scalar fitness score.

    Separation of concerns: this class knows nothing about genetic operators
    (selection, crossover, mutation) or the fuzzy controller.  It is the sole
    authoritative source of fitness values for the GA.

    Parameters
    ----------
    scenario:
        The road-network scenario containing nodes, edges, and demand data.
    distance_weight:
        Weight applied to normalised total distance in the fitness formula.
    time_weight:
        Weight applied to normalised total travel time.
    penalty_weight:
        Weight applied to normalised constraint-violation penalty.

    Notes
    -----
    Graph rebuilds are amortised O(1) when the scenario is not disrupted; a
    single call to :meth:`invalidate_cache` marks the graph as stale so the
    next :meth:`evaluate_route` call triggers a rebuild.
    """

    def __init__(
        self,
        scenario: NetworkScenarioModel,
        distance_weight: float = DEFAULT_DISTANCE_WEIGHT,
        time_weight: float = DEFAULT_TIME_WEIGHT,
        penalty_weight: float = DEFAULT_PENALTY_WEIGHT,
    ) -> None:
        self.scenario = scenario
        self.w_d = distance_weight  # Distance component weight
        self.w_t = time_weight      # Travel-time component weight
        self.w_p = penalty_weight   # Penalty component weight

        # ------------------------------------------------------------------ #
        # Pre-compute normalisation scales once from static scenario geometry #
        # ------------------------------------------------------------------ #
        node_count = max(4, len(scenario.nodes))

        xs = [n.x for n in scenario.nodes.values()]
        ys = [n.y for n in scenario.nodes.values()]

        # Euclidean bounding-box diagonal → approximate worst-case single leg
        diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) if xs and ys else 100.0

        # dist_scale: rough upper bound on total route distance for normalisation
        self.dist_scale: float = max(10.0, node_count * (diag / 3.0))

        # time_scale: convert dist_scale to minutes assuming average 40 km/h speed
        self.time_scale: float = max(10.0, (self.dist_scale / 40.0) * 60.0)

        # penalty_scale: sigmoid-style denominator keeping p_norm ∈ (0, 1)
        self.penalty_scale: float = 100.0

        # ------------------------------------------------------------------ #
        # Lazy graph cache                                                    #
        # ------------------------------------------------------------------ #
        self._active_graph: Optional[nx.Graph] = None
        self._graph_dirty: bool = True  # Force rebuild on first call

    # ---------------------------------------------------------------------- #
    # Cache management                                                        #
    # ---------------------------------------------------------------------- #

    def invalidate_cache(self) -> None:
        """Mark the graph cache as stale.

        Must be called whenever scenario edge state changes (roads blocked,
        traffic factors updated, etc.).  The next call to
        :meth:`get_navigable_graph` will trigger a full O(|V|+|E|) rebuild.

        Complexity
        ----------
        Time : O(1).
        Space: O(1).
        """
        self._graph_dirty = True

    # ---------------------------------------------------------------------- #
    # Graph construction                                                      #
    # ---------------------------------------------------------------------- #

    def get_navigable_graph(self) -> nx.Graph:
        """Return a ``networkx.Graph`` containing only currently passable edges.

        Edges are weighted by *effective travel time* (base travel time
        multiplied by the current ``traffic_factor``), which is the primary
        Dijkstra search criterion.  Blocked edges are excluded entirely.

        This method is **O(1)** on a cache hit and **O(|V| + |E|)** on a
        cache miss (graph rebuild).

        Returns
        -------
        nx.Graph
            Undirected weighted graph ready for ``nx.shortest_path`` queries.

        Complexity
        ----------
        Time : O(|V| + |E|) rebuild, O(1) cached.
        Space: O(|V| + |E|) for the graph object.
        """
        if not self._graph_dirty and self._active_graph is not None:
            return self._active_graph  # O(1) cache hit

        # O(|V|) — add all nodes with positional metadata
        g: nx.Graph = nx.Graph()
        for nid, node in self.scenario.nodes.items():
            g.add_node(nid, x=node.x, y=node.y, priority=node.priority)

        # O(|E|) — add only unblocked edges; set Dijkstra weight = effective time
        for edge in self.scenario.edges:
            if not edge.blocked:
                # Effective travel time reflects real-time congestion
                eff_time: float = edge.travel_time * edge.traffic_factor
                g.add_edge(
                    edge.source,
                    edge.target,
                    distance=edge.distance,
                    travel_time=eff_time,
                    weight=eff_time,  # Primary Dijkstra traversal criterion
                )

        self._active_graph = g
        self._graph_dirty = False
        return g

    # ---------------------------------------------------------------------- #
    # Route evaluation                                                        #
    # ---------------------------------------------------------------------- #

    def evaluate_route(self, candidate: List[int]) -> RouteEvaluation:
        """Evaluate a candidate permutation and return a :class:`RouteEvaluation`.

        The candidate is interpreted as an ordered list of customer node IDs.
        The depot (ID = ``scenario.depot_id``) is automatically prepended and
        appended so the full physical route forms a *closed loop*.

        For each consecutive pair of stops ``(u, v)`` Dijkstra is run on the
        navigable graph to find the minimum-time sub-path.  If no path exists
        (due to blocked roads), a Euclidean fallback distance estimate is used
        and the route is marked infeasible.

        Fitness formula (all terms normalised to ≈ [0, 1]):

        .. math::
            F = w_d \\cdot \\hat{D} + w_t \\cdot \\hat{T} + w_p \\cdot \\hat{P}

        where :math:`\\hat{D}`, :math:`\\hat{T}`, :math:`\\hat{P}` are
        normalised distance, travel time, and penalty respectively.

        Parameters
        ----------
        candidate:
            Ordered permutation of customer node IDs (depot excluded or
            included — the method normalises both forms).

        Returns
        -------
        RouteEvaluation
            Pydantic model containing the raw and normalised metrics, the full
            detailed path, and a feasibility flag.

        Complexity
        ----------
        Time : O(k * (|V| log |V| + |E|)) where k = len(candidate) − 1.
        Space: O(|V| + |E|) for the cached graph plus O(k * L) for paths.
        """
        if not candidate:
            # Return a maximally penalised infeasible evaluation
            return RouteEvaluation(
                node_sequence=[],
                total_distance=1e6,
                total_travel_time=1e6,
                constraint_penalty=1e6,
                fitness=1e6,
                is_feasible=False,
            )

        # ------------------------------------------------------------------ #
        # Step 1: Normalise sequence — ensure Depot → [Customers] → Depot    #
        # ------------------------------------------------------------------ #
        seq: List[int] = list(candidate)
        if seq[0] != self.scenario.depot_id:
            seq = [self.scenario.depot_id] + seq
        if seq[-1] != self.scenario.depot_id:
            seq = seq + [self.scenario.depot_id]

        # ------------------------------------------------------------------ #
        # Step 2: Retrieve (or rebuild) the navigable graph — O(1) or O(|E|) #
        # ------------------------------------------------------------------ #
        g: nx.Graph = self.get_navigable_graph()

        # ------------------------------------------------------------------ #
        # Step 3: Dijkstra routing between consecutive stops                 #
        # ------------------------------------------------------------------ #
        # O(k * (|V| log |V| + |E|)) total — k = number of stop pairs
        detailed_path: List[int] = [seq[0]]
        total_distance: float = 0.0
        total_time: float = 0.0
        penalty: float = 0.0
        is_feasible: bool = True
        traversed_edges: List[Tuple[int, int]] = []
        unreachable_segments: List[Tuple[int, int]] = []

        for i in range(len(seq) - 1):
            u, v = seq[i], seq[i + 1]
            if u == v:
                continue  # Identical consecutive stops → skip

            try:
                # Dijkstra shortest-path on current navigable graph
                # O(|V| log |V| + |E|) per pair via networkx's heap implementation
                path: List[int] = nx.shortest_path(g, source=u, target=v, weight="weight")

                # Accumulate physical metrics along the Dijkstra sub-path
                for step in range(len(path) - 1):
                    p_u, p_v = path[step], path[step + 1]
                    edge_data: Dict = g.get_edge_data(p_u, p_v)
                    total_distance += edge_data.get("distance", 0.0)
                    total_time += edge_data.get("travel_time", 0.0)
                    traversed_edges.append((min(p_u, p_v), max(p_u, p_v)))
                    if step > 0:
                        detailed_path.append(p_u)
                detailed_path.append(v)

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # Segment unreachable → mark infeasible, apply large penalty
                is_feasible = False
                unreachable_segments.append((u, v))
                penalty += PENALTY_UNREACHABLE_SEGMENT

                # Euclidean fallback so fitness remains a finite, comparable number
                n_u = self.scenario.nodes[u]
                n_v = self.scenario.nodes[v]
                fallback_dist: float = math.hypot(n_u.x - n_v.x, n_u.y - n_v.y)
                total_distance += fallback_dist * 2.0          # Penalise detour
                total_time += (fallback_dist / 20.0) * 60.0   # Assume slow crawl
                detailed_path.append(v)

        # ------------------------------------------------------------------ #
        # Step 4: Constraint penalties (priority ordering)                   #
        # ------------------------------------------------------------------ #
        priority_penalty: float = evaluate_priority_penalty(seq, self.scenario.nodes)
        penalty += priority_penalty

        # ------------------------------------------------------------------ #
        # Step 5: Normalise and compute composite fitness                    #
        # ------------------------------------------------------------------ #
        # Normalise each term to ≈ [0, 1] for weight comparability
        d_norm: float = total_distance / self.dist_scale
        t_norm: float = total_time / self.time_scale
        # Sigmoid-style penalty normalisation: p/(p+scale) ∈ (0, 1) for p > 0
        p_norm: float = penalty / (penalty + self.penalty_scale) if penalty > 0 else 0.0

        # Weighted multi-objective sum — lower is better
        fitness: float = round(
            self.w_d * d_norm + self.w_t * t_norm + self.w_p * p_norm, 4
        )

        return RouteEvaluation(
            node_sequence=seq,
            detailed_path=detailed_path,
            total_distance=round(total_distance, 2),
            total_travel_time=round(total_time, 2),
            constraint_penalty=round(penalty, 2),
            fitness=fitness,
            is_feasible=is_feasible,
            traversed_edges=traversed_edges,
            unreachable_segments=unreachable_segments,
        )
