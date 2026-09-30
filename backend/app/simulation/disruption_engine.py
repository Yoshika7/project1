"""
Disruption Engine for AdaptIQ-R.
Simulates road blocks, traffic surges, customer priority changes, and vehicle failures.
Computes real normalized disruption severity based on physical network changes.
"""

from typing import List, Tuple, Optional, Dict
from backend.app.core.models import (
    NetworkScenarioModel,
    DisruptionSeverity,
    DisruptionEvent,
    DisruptionType
)
from backend.app.core.config import (
    SEVERITY_WEIGHT_BLOCKED,
    SEVERITY_WEIGHT_TRAFFIC,
    SEVERITY_WEIGHT_PRIORITY,
    SEVERITY_WEIGHT_VEHICLE
)
from backend.app.simulation.traffic import calculate_traffic_change_ratio, apply_traffic_surge


class DisruptionEngine:
    """
    Manages active disruptions and computes quantitative disruption severity.
    """

    def __init__(self, scenario: NetworkScenarioModel):
        self.scenario = scenario
        self.events: List[DisruptionEvent] = []
        self.initial_edge_count = len(scenario.edges)
        self.initial_node_count = len(scenario.nodes)
        self.initial_priorities: Dict[int, int] = {
            nid: node.priority for nid, node in scenario.nodes.items()
        }
        self.vehicle_capacity_ratio: float = 1.0  # 1.0 = 100% capacity available

    def block_road(self, source: int, target: int, description: str = "") -> DisruptionSeverity:
        """
        Blocks an edge between source and target in both directions.
        """
        pair = (min(source, target), max(source, target))
        found = False
        for edge in self.scenario.edges:
            edge_pair = (min(edge.source, edge.target), max(edge.source, edge.target))
            if edge_pair == pair:
                edge.blocked = True
                found = True

        if not found:
            raise ValueError(f"Edge ({source}, {target}) does not exist in network.")

        desc = description or f"Road {source} <-> {target} BLOCKED"
        self.events.append(DisruptionEvent(
            disruption_type="road_block",
            target_id=f"{source}-{target}",
            value=True,
            description=desc
        ))
        return self.calculate_severity()

    def unblock_road(self, source: int, target: int) -> DisruptionSeverity:
        """
        Restores an edge to unblocked state.
        """
        pair = (min(source, target), max(source, target))
        for edge in self.scenario.edges:
            edge_pair = (min(edge.source, edge.target), max(edge.source, edge.target))
            if edge_pair == pair:
                edge.blocked = False
        return self.calculate_severity()

    def inject_traffic_surge(
        self,
        edges: List[Tuple[int, int]],
        factor: float = 2.5,
        description: str = ""
    ) -> DisruptionSeverity:
        """
        Increases congestion factor on selected edges.
        """
        apply_traffic_surge(self.scenario, edges, factor)
        desc = description or f"Traffic surge {factor}x on {len(edges)} edge(s)"
        self.events.append(DisruptionEvent(
            disruption_type="traffic_surge",
            target_id=str(edges),
            value=factor,
            description=desc
        ))
        return self.calculate_severity()

    def change_node_priority(
        self,
        node_id: int,
        new_priority: int = 3,
        description: str = ""
    ) -> DisruptionSeverity:
        """
        Modifies delivery priority for a node.
        """
        if node_id not in self.scenario.nodes:
            raise ValueError(f"Node {node_id} not found in scenario.")

        node = self.scenario.nodes[node_id]
        node.priority = new_priority
        node.type = "priority" if new_priority > 1 else "customer"

        desc = description or f"Node {node_id} priority set to {new_priority}"
        self.events.append(DisruptionEvent(
            disruption_type="priority_change",
            target_id=str(node_id),
            value=new_priority,
            description=desc
        ))
        return self.calculate_severity()

    def simulate_vehicle_failure(
        self,
        capacity_loss_fraction: float = 0.5,
        description: str = ""
    ) -> DisruptionSeverity:
        """
        Simulates vehicle breakdown reducing fleet capacity.
        """
        self.vehicle_capacity_ratio = max(0.0, 1.0 - capacity_loss_fraction)
        desc = description or f"Vehicle failure: fleet capacity reduced by {int(capacity_loss_fraction*100)}%"
        self.events.append(DisruptionEvent(
            disruption_type="vehicle_failure",
            target_id="fleet",
            value=capacity_loss_fraction,
            description=desc
        ))
        return self.calculate_severity()

    def calculate_severity(self) -> DisruptionSeverity:
        """
        Calculates normalized disruption severity S in [0, 1] using:
        S = 0.40 * blocked_edge_ratio + 0.30 * normalized_traffic_change
            + 0.15 * normalized_priority_change + 0.15 * vehicle_change
        """
        total_edges = max(1, len(self.scenario.edges))
        blocked_count = sum(1 for e in self.scenario.edges if e.blocked)
        blocked_edge_ratio = blocked_count / float(total_edges)

        traffic_change_ratio = calculate_traffic_change_ratio(self.scenario)

        # Priority change ratio: fraction of customer nodes with increased priority
        priority_changes = 0
        customer_nodes = [nid for nid in self.scenario.nodes if nid != 0]
        total_customers = max(1, len(customer_nodes))
        for nid in customer_nodes:
            current_p = self.scenario.nodes[nid].priority
            initial_p = self.initial_priorities.get(nid, 1)
            if current_p != initial_p:
                priority_changes += 1
        priority_change_ratio = min(1.0, priority_changes / float(total_customers))

        # Vehicle capacity change
        vehicle_change = max(0.0, min(1.0, 1.0 - self.vehicle_capacity_ratio))

        severity_raw = (
            SEVERITY_WEIGHT_BLOCKED * blocked_edge_ratio +
            SEVERITY_WEIGHT_TRAFFIC * traffic_change_ratio +
            SEVERITY_WEIGHT_PRIORITY * priority_change_ratio +
            SEVERITY_WEIGHT_VEHICLE * vehicle_change
        )
        severity_clamped = min(1.0, max(0.0, severity_raw))

        return DisruptionSeverity(
            severity=round(severity_clamped, 4),
            blocked_edge_ratio=round(blocked_edge_ratio, 4),
            normalized_traffic_change=round(traffic_change_ratio, 4),
            normalized_priority_change=round(priority_change_ratio, 4),
            vehicle_change=round(vehicle_change, 4)
        )
