"""module containing util for calculating the shortest path between two aspects"""

from __future__ import annotations
from dataclasses import dataclass

from .aspect import Aspect

@dataclass
class Node():
    aspect: Aspect
    paths: dict[str, Node]

    def __str__(self) -> str:
        return f"{self.aspect.name}: {self.paths}"

class Graph():
    def __init__(self, aspects: list[Aspect]):
        self._nodes = {}
        for aspect in aspects:
            self._nodes[aspect.name] = Node(aspect, {})

        self.is_constructed = False
    
    _nodes: dict[str, Node]

    def get_nodes(self) -> list[Node]:
        return [item for item in self._nodes.values()]
    
    def get_node(self, node_name: str) -> Node:
        if not isinstance(node_name, str):
            raise TypeError()

        return self._nodes[node_name]

    def set_path(self, node_name: str, target_node_name: str, next_neighbor_name: str):
        if not isinstance(node_name, str) or not isinstance(target_node_name, str) or not isinstance(next_neighbor_name, str):
            raise TypeError()

        if not self.node_knows_path_to_node(self.get_node(node_name), self.get_node(next_neighbor_name)):
            raise RuntimeError(f"node {node_name} doesn't know a way to node {next_neighbor_name}")
        if not self.node_knows_path_to_node(self.get_node(next_neighbor_name), self.get_node(target_node_name)):
            raise RuntimeError(f"node {next_neighbor_name} doesn't know a way to node {target_node_name}")
        
        if node_name == "Humanus":
            print(node_name, target_node_name, next_neighbor_name)

        self._nodes[node_name].paths[target_node_name] = self.get_node(next_neighbor_name)

    def node_knows_path_to_node(self, node: Node, other_node: Node) -> bool:
        return node.aspect.name == other_node.aspect.name or \
               other_node.aspect.name in [item.name for item in node.aspect.neighbors] or \
               other_node.aspect.name in node.paths.keys()

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
            if not target_node_name in curr_node.paths.keys():
                raise Exception(f"path to node {target_node_name} not found in node {curr_node.aspect.name}")
            path.append(curr_node.aspect)
            curr_node = curr_node.paths[target_node_name]
        
        path.append(self._nodes[target_node_name].aspect)
        return path

    def calc_graph(self, iterations: int = 20):
        # add all neighbors to the paths
        for node in self.get_nodes():
            for neighbor_aspect in node.aspect.neighbors:
                if not neighbor_aspect.name in node.paths.keys():
                    self.set_path(node.aspect.name, neighbor_aspect.name, neighbor_aspect.name)

        for _ in range(iterations):
            for node in self.get_nodes():
                for other_node in self.get_nodes():
                    if node.aspect.name == other_node.aspect.name:
                        continue
                    if not self.node_knows_path_to_node(node, other_node):
                        continue

                    self._exchange_paths(node, other_node)

        self.is_constructed = True

    def _exchange_paths(self, node: Node, other_node: Node):
        """Adds all missing or cheaper paths from other_node to node"""

        for node_name in other_node.paths.keys():
            if node_name == node.aspect.name:
                continue

            # add path if node doesn't know others node
            if not self.node_knows_path_to_node(node, self.get_node(node_name)):
                self.set_path(node.aspect.name, node_name, other_node.aspect.name)
                continue

            new_path_cost = self.calc_cost(other_node.aspect.name, node_name) - other_node.aspect.cost + self.calc_cost(node.aspect.name, other_node.aspect.name)
            old_path_cost = self.calc_cost(node.aspect.name, node_name)

            if new_path_cost < old_path_cost:
                self.set_path(node.aspect.name, node_name, other_node.aspect.name)

class ShortestPath2():
    """class for calculating the shortest path between two aspects"""

    def __init__(self, aspects: list[Aspect]) -> None:
        self._aspects = aspects
        self.graph = Graph(aspects)
        self.graph.calc_graph()

    counter = 0 # for performance testing
    graph: Graph

    def print_to_file(self):
        with open("graph.txt", "w+") as f:
            for node in self.graph.values():
                f.write(str(node) + "\n")
