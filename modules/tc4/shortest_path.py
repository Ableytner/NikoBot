from .aspect import Aspect

class ShortestPath():
    def __init__(self, aspects: list[Aspect]) -> None:
        self._aspects = aspects
    
    def recursive(self, curr: Aspect, goal: Aspect, path = None, depth = 0) -> list[Aspect] | None:
        if path is None:
            path = []
        
        path.append(curr)
        
        if goal in curr.neighbors:
            path.append(goal)
            return path

        paths = []
        for aspect in curr.neighbors:
            if aspect not in path:
                new_path = self.recursive(aspect, goal, path.copy(), depth + 1)
                if new_path is not None:
                    paths.append((new_path, self.calc_cost(new_path)))
        
        if len(paths) == 0:
            return None

        paths.sort(key=lambda x: x[1])

        return paths[0][0]

    def calc_cost(self, path: list[Aspect]) -> float:
        cost = 0
        for aspect in path:
            cost += aspect.cost
        return cost
