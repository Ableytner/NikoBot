"""module containing util for calculating the shortest path between two aspects"""

from __future__ import annotations
from dataclasses import dataclass

from .aspect import Aspect

@dataclass
class Node():
    aspect: Aspect
    routes: dict[str, Node]

    def set_route(self, target_node_name: str, next_node_name: Node):
        """
        Set a route to 'target_node_name' using 'next_node_name'
        as the node which holds information for the rest of the path
        """

        if not isinstance(target_node_name, str) or not isinstance(next_node_name, Node):
            raise TypeError()

        self.routes[target_node_name] = next_node_name

    def __str__(self) -> str:
        printable_routes = {key: value.aspect.name for key, value in self.routes.items()}
        return f"{self.aspect.name}: {printable_routes}"

class Graph():
    def __init__(self, aspects: list[Aspect]):
        self._nodes = {}
        for aspect in aspects:
            self._nodes[aspect.name] = Node(aspect, {})
    
    _nodes: dict[str, Node]

    def is_constructed(self) -> bool:
        if self._nodes is None or len(self._nodes) == 0:
            return False

        complete = True
        for node in self.get_nodes():
            # ignore the route to the node itself
            if len(node.routes) < len(self.get_nodes()) - 1:
                complete = False
        return complete

    def get_nodes(self, iter = None) -> list[Node]:
        """
        Convert a given list of aspects or aspect names to nodes.
        Return all nodes in the graph if iter is None.
        """

        if iter is None:
            return [item for item in self._nodes.values()]
        else:
            nodes = []
            for item in iter:
                nodes.append(self.get_node(item))
            return nodes
    
    def get_node(self, node_name: str | Aspect) -> Node:
        if not isinstance(node_name, (str, Aspect)):
            raise TypeError()
        
        if isinstance(node_name, Aspect):
            node_name = node_name.name

        return self._nodes[node_name]

    def calc_cost(self, start_node_name: str, target_node_name: str) -> int:
        if not isinstance(start_node_name, str) or not isinstance(target_node_name, str):
            raise TypeError()

        path = self.calc_shortest_path(start_node_name, target_node_name)
        cost = 0

        for aspect in path:
            cost += aspect.cost
        
        return cost

    def calc_shortest_path(self, start_node_name: str, target_node_name: str) -> list[Aspect]:
        if not isinstance(start_node_name, str) or not isinstance(target_node_name, str):
            raise TypeError()

        start_node = self.get_node(start_node_name)
        curr_node = start_node
        path = []

        while curr_node.aspect.name != target_node_name:
            if not target_node_name in curr_node.routes.keys():
                raise Exception(f"route to node {target_node_name} not found in node {curr_node.aspect.name}")

            path.append(curr_node.aspect)
            curr_node = curr_node.routes[target_node_name]
        
        path.append(self._nodes[target_node_name].aspect)
        return path

    def construct(self):
        # add all neighbors to the routing table
        for node in self.get_nodes():
            for neighbor_aspect in node.aspect.neighbors:
                if not neighbor_aspect.name in node.routes.keys():
                    node.set_route(neighbor_aspect.name, self.get_node(neighbor_aspect))

        c = 0
        while c < 20:
            c += 1
            for node in self.get_nodes():
                for neighbor_node in self.get_nodes(node.aspect.neighbors):
                    self._exchange_paths(node, neighbor_node)

    def _exchange_paths(self, node: Node, other_node: Node) -> None:
        """Adds all missing or cheaper paths from other_node to node"""

        for node_name in other_node.routes.keys():
            if node_name == node.aspect.name:
                continue

            # add route if node doesn't know a way
            if node_name not in node.routes.keys():
                node.set_route(node_name, other_node)
            # change route if new route is cheaper
            else:
                old_path_cost = self.calc_cost(node.aspect.name, node_name)
                new_path_cost = node.aspect.cost + self.calc_cost(other_node.routes[node_name].aspect.name, node_name)

                if new_path_cost < old_path_cost:
                    node.set_route(node_name, other_node)
