"""module containing the AspectParser class"""

from .aspect import Aspect

class AspectParser():
    """class for parsing the aspects.txt file to aspect objects"""

    def __init__(self, filename: str) -> None:
        self._filename = filename

    def parse(self) -> dict[str, Aspect]:
        """parse the aspects, returning a aspect_name: Aspect dictionary"""

        result: dict[str, Aspect] = {}

        with open(self._filename, "r") as f:
            remaining_lines = f.readlines()

        while len(remaining_lines) > 0:
            component1 = None
            component2 = None
            aspect_to_add = None
            cost = 10
            line_split = remaining_lines[0].strip("\n").split(",")

            # a custom cost is given
            if len(line_split) % 2 == 1:
                cost = int(line_split.pop())

            # the aspect is primal
            if len(line_split) == 2:
                aspect_to_add = Aspect(*line_split, cost=cost)
            # the aspect is not primal
            elif len(line_split) == 4:
                if line_split[2] in result.keys() and line_split[3] in result.keys():
                    for aspect in result.values():
                        if aspect.name == line_split[2]:
                            component1 = aspect
                        if aspect.name == line_split[3]:
                            component2 = aspect

                    if component1 is not None and component2 is not None:
                        aspect_to_add = Aspect(line_split[0], line_split[1], cost, component1, component2)
            
            if aspect_to_add is not None:
                result[aspect_to_add.name] = aspect_to_add
                remaining_lines.pop(0)
            else:
                # move aspect to the back of the list
                remaining_lines.append(remaining_lines.pop(0))

        return result
