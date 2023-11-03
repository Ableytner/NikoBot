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
                    node.paths[nb.name] = Path(nb.name, 0)
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

                    if node1.aspect.name == "Potentia" and node2.aspect.name == "Vitium":
                        pass
                    # print(f"c1: {c1}, c2: {c2}", end="\r")

                    # ignore if the nodes are the same
                    if c1 == c2:
                        c2 += 1
                        continue

                    # skip if no path between the two nodes is knwon
                    if not node1.aspect.name in node2.paths.keys() or not node2.aspect.name in node1.paths.keys():
                        c2 += 1
                        continue

                    self._exchange_paths(node1, node2)
                    self._exchange_paths(node2, node1)

                    c2 += 1

                # if the node has paths to all other nodes, remove it
                if len(node1.paths) >= len(self.all_nodes) - 1:
                    node_name = remaining_names.pop(c1)
                    self.graph[node_name] = self.all_nodes[node_name]
                    c1 -= 1

                c1 += 1

    def _exchange_paths(self, curr_node: Node, other_node: Node):
        """Adds all missing or cheaper paths from other_node to curr_node"""
        for node_name in other_node.paths.keys():
            if node_name == curr_node.aspect.name or other_node.paths[node_name].next_node == curr_node.aspect.name:
                continue

            try:
                new_path_cost = self._calc_cost(other_node, self.all_nodes[node_name]) + other_node.aspect.cost + self._calc_cost(curr_node, other_node)
            except RecursionError:
                pass

            if not node_name in curr_node.paths.keys():
                sp = self.recursive(curr_node, other_node)[1::] + self.recursive(other_node, self.all_nodes[node_name])

                full_path_is_known = True
                path_is_recursive = False
                for sp_aspect in sp[1:-1:]:
                    sp_node = self.all_nodes[sp_aspect.name]
                    if node_name not in sp_node.paths.keys():
                        full_path_is_known = False
                    if curr_node.aspect.name == sp_aspect.name:
                        path_is_recursive = True
                
                if full_path_is_known and not path_is_recursive:
                    curr_node.paths[node_name] = Path(sp[1].name, new_path_cost)
            else:
                try:
                    curr_path_cost = self._calc_cost(curr_node, self.all_nodes[node_name])
                except RecursionError:
                    pass

                if curr_path_cost > new_path_cost:
                    sp = self.recursive(curr_node, other_node)[1::] + self.recursive(other_node, self.all_nodes[node_name])

                    full_path_is_known = True
                    path_is_recursive = False
                    for sp_aspect in sp[1:-1:]:
                        sp_node = self.all_nodes[sp_aspect.name]
                        if node_name not in sp_node.paths.keys():
                            full_path_is_known = False
                        if curr_node.aspect.name == sp_aspect.name:
                            path_is_recursive = True

                    if full_path_is_known and not path_is_recursive:
                        curr_node.paths[node_name] = Path(sp[1].name, new_path_cost)
                else:
                    pass

    def _calc_cost(self, start_node: Node, goal_node: Node):
        cost = 0
        sp = self.recursive(start_node, goal_node)

        # ignore the current nodes cost
        for aspect in sp[1:-1:]:
            cost += aspect.cost
        
        return cost

    def recursive(self, curr: Node, goal: Node, path = None) -> list[Aspect] | None: # pylint: disable=line-too-long
        """
        calculate the shortest path, returning a list of aspects representing the shortest path
        """

        if path is None:
            path = []
        c = 0
        while curr.aspect.name != goal.aspect.name:
            ShortestPath2.counter += 1
            c += 1
            if c > 1000:
                raise RecursionError()

            path.append(curr.aspect)

            curr = self.all_nodes[curr.paths[goal.aspect.name].next_node]

        path.append(curr.aspect)
        return path

    def print_to_file(self):
        with open("graph.txt", "w+") as f:
            for node in self.graph.values():
                f.write(str(node) + "\n")
