"""module containing util for calculating the shortest path between two aspects"""

from __future__ import annotations

from dataclasses import dataclass

from .aspect import Aspect
from .aspect_parser import AspectParser

@dataclass
class Node():
    aspect: Aspect
    paths: dict[str, Path]

    def __str__(self) -> str:
        return f"{self.aspect.name}: {self.paths}"

@dataclass
class Path():
    next_node: str
    cost: int # the total cost to reach the node

class ShortestPath2():
    """class for calculating the shortest path between two aspects"""

    def __init__(self, aspects: list[Aspect]) -> None:
        self._aspects = aspects
        self.graph = {}
        self.all_nodes = {}

    counter = 0 # for performance testing
    graph: dict[str, Node]
    all_nodes: dict[str, Node]

    def calculate_graph(self):
        for aspect in self._aspects:
            self.all_nodes[aspect.name] = Node(aspect, {})

        # add all neighbors to the paths
        for node in self.all_nodes.values():
            if node.aspect.name == "Lucrum":
                pass
            for nb in node.aspect.neighbors:
                if not nb.name in node.paths.keys():
                    node.paths[nb.name] = Path(nb.name, nb.cost)
        del node, nb
        
        remaining_names = list(self.all_nodes.keys())

        while len(remaining_names) > 0:
            for i, name in enumerate(remaining_names):
                if len(self.all_nodes[name].paths) >= len(self.all_nodes) - 1:
                    self.graph[name] = self.all_nodes[remaining_names.pop(i)]

            c1 = 0
            while c1 < len(remaining_names): # curr_node in self.all_nodes.values():
                node1: Node = self.all_nodes[remaining_names[c1]]

                c2 = 0
                while c2 < len(remaining_names): # for target_node_name in curr_node.paths.keys():
                    node2: Node = self.all_nodes[remaining_names[c2]]

                    if node1.aspect.name == "Nebrisum" and node2.aspect.name == "Nebrisum":
                        pass
                    # print(f"c1: {c1}, c2: {c2}", end="\r")

                    # ignore if the nodes are the same
                    if c1 == c2:
                        c2 += 1
                        continue

                    # skiip if no path between the two nodes is knwon
                    if not node1.aspect.name in node2.paths.keys():
                        c2 += 1
                        continue

                    self._exchange_paths(node1, node2)

                    if len(node1.paths) >= len(self.all_nodes) - 1:
                        node_name = remaining_names.pop(c1)
                        self.graph[node_name] = self.all_nodes[node_name]
                        c1 -= 1
                        break

                    if len(node2.paths) >= len(self.all_nodes) - 1:
                        node_name = remaining_names.pop(c2)
                        self.graph[node_name] = self.all_nodes[node_name]
                        continue

                    c2 += 1
                c1 += 1

    def _exchange_paths(self, curr_node: Node, other_node: Node):
        for node_name, other_path in other_node.paths.items():
            if node_name == curr_node.aspect.name:
                continue

            if not node_name in curr_node.paths.keys():
                curr_node.paths[node_name] = Path(other_node.aspect.name, other_path.cost + other_node.aspect.cost)
            else:
                if curr_node.paths[node_name].cost > other_path.cost + other_node.aspect.cost:
                    curr_node.paths[node_name] = Path(other_node.aspect.name, other_path.cost + other_node.aspect.cost)
                else:
                    pass

        for node_name, curr_path in curr_node.paths.items():
            if node_name == other_node.aspect.name:
                continue

            if not node_name in other_node.paths.keys():
                other_node.paths[node_name] = Path(curr_node.aspect.name, curr_path.cost + curr_node.aspect.cost)
            else:
                if other_node.paths[node_name].cost > curr_path.cost + curr_node.aspect.cost:
                    other_node.paths[node_name] = Path(curr_node.aspect.name, curr_path.cost + curr_node.aspect.cost)
                else:
                    pass

    def recursive(self, curr: Node, goal: Node, path = None) -> list[Aspect] | None: # pylint: disable=line-too-long
        """
        calculate the shortest path, returning a list representing the shortest path
        every element is the aspect node and the total cost till this point
        """

        ShortestPath2.counter += 1

        if path is None:
            path = []

        path.append(curr.aspect)

        if curr.aspect.name == goal.aspect.name:
            return path

        return self.recursive(self.all_nodes[curr.paths[goal.aspect.name].next_node], goal, path)

    def print_to_file(self):
        with open("graph.txt", "w+") as f:
            for node in self.graph.values():
                f.write(str(node) + "\n")
