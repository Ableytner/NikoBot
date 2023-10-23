"""module containing util for calculating the shortest path between two aspects"""

from .aspect import Aspect

class ShortestPath():
    """class for calculating the shortest path between two aspects"""

    def __init__(self, aspects: list[Aspect]) -> None:
        self._aspects = aspects

    counter = 0

    def recursive(self, curr: Aspect, goal: Aspect, path = None, cost = 0) -> list[tuple[Aspect, int]] | None: # pylint: disable=line-too-long
        """
        calculate the shortest path, returning a list representing the shortest path
        every element is the aspect node and the total cost till this point
        """

        ShortestPath.counter += 1

        if path is None:
            path = []

        if len(path) > 15:
            return None

        path.append(curr)

        if goal in curr.neighbors:
            path.append(goal)
            return (path, cost)

        cost += curr.cost

        paths = []
        for aspect in curr.neighbors:
            if aspect not in path:
                new_path = self.recursive(aspect, goal, path.copy(), cost)
                if new_path is not None:
                    paths.append(new_path)

        if len(paths) == 0:
            return None

        paths.sort(key=lambda x: x[1])

        return paths[0]

    def calc_cost(self, path: list[Aspect]) -> float:
        """calculate the cost of a given list of aspects"""

        cost = 0
        for aspect in path:
            cost += aspect.cost
        return cost
