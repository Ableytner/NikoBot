import time
import os

from modules.tc4.aspect import Aspect
from modules.tc4.aspect_parser import AspectParser
from modules.tc4.shortest_path import ShortestPath

class PerformanceTest():
    def __init__(self) -> None:
        parser = AspectParser("modules/tc4/aspects.txt")
        self.aspects = parser.parse()
        for aspect in self.aspects.values():
            aspect.construct_neighbors(self.aspects)

    def path(self, aspect_name_1: str | Aspect, aspect_name_2: str | Aspect):
        aspect_objs = [self._find_aspect(aspect_name_1) if isinstance(aspect_name_1, str) else aspect_name_1, self._find_aspect(aspect_name_2) if isinstance(aspect_name_2, str) else aspect_name_2]
        assert all(aspect_objs)

        return ShortestPath(self.aspects).recursive(*aspect_objs)

    def _find_aspect(self, aspect_name: str) -> Aspect | None:
        aspect_name = aspect_name.capitalize()
        aspect_obj = None

        if aspect_name in self.aspects.keys():
            aspect_obj = self.aspects[aspect_name]

        for aspect in self.aspects.values():
            if aspect.keyword == aspect_name.lower():
                aspect_obj = aspect
        
        return aspect_obj

def test_path_all():
    with open("perf_test.txt", "w+"):
        pass

    pt = PerformanceTest()
    c = 0
    rec_c = 0

    for aspect1 in pt.aspects:
        for aspect2 in pt.aspects:
            st = time.time()
            path = pt.path(aspect1, aspect2)
            text = f"Execution time: {'%6.0f' % int((time.time()-st)*1000)}ms | "
            text += f"Recursions: {'%9.0f' % ShortestPath.counter} | "
            text += str(path) + "\n"
            with open("perf_test.txt", "a") as f:
                f.write(text)

            c += 1
            print(f"Finished {c}/{len(pt.aspects)**2} paths", end="\r")

            rec_c += ShortestPath.counter
            ShortestPath.counter = 0

    print(f"Finished {c}/{len(pt.aspects)**2} paths")
    return rec_c

if __name__ == "__main__":
    st = time.time()
    rec_c = test_path_all()
    print(f"Total execution time: {int((time.time()-st))}s")
    print(f"Total recursions: {rec_c}")
