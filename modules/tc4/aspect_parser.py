from .aspect import Aspect

class AspectParser():
    def __init__(self, filename: str) -> None:
        self._filename = filename

    def parse(self) -> dict[str, Aspect]:
        parsed_lines: list[Aspect] = []
        parsed_names = []

        with open(self._filename, "r") as f:
            remaining_lines = f.readlines()
        
        # last_remaining = len(remaining_lines)
        i = 0
        while len(remaining_lines) > 0:
            component1 = None
            component2 = None
            aspect_to_add = None
            cost = 10
            line_split = remaining_lines[i].strip("\n").split(",")

            if len(line_split) % 2 == 1:
                cost = int(line_split.pop())
                # cost = int((1 / cost) * 10)

            if len(line_split) == 2:
                aspect_to_add = Aspect(*line_split, cost=cost)

            elif len(line_split) == 4:
                if line_split[2] in parsed_names and line_split[3] in parsed_names:
                    for aspect in parsed_lines:
                        if aspect.name == line_split[2]:
                            component1 = aspect
                        if aspect.name == line_split[3]:
                            component2 = aspect

                    if component1 is not None and component2 is not None:
                        aspect_to_add = Aspect(line_split[0], line_split[1], cost, component1, component2)
            
            if aspect_to_add is not None:
                parsed_lines.append(aspect_to_add)
                parsed_names.append(aspect_to_add.name)
                remaining_lines.pop(i)

            i += 1
            if i >= len(remaining_lines):
                i = 0
            
            # if len(remaining_lines) != last_remaining:
                # last_remaining = len(remaining_lines)
                # print(f"remaining: {last_remaining}")
                # print(f"parsed_names: {parsed_names}")
                # print(f"parsed_lines: {parsed_lines}")

        return {aspect.name: aspect for aspect in parsed_lines}
