# pylint: skip-file

from src.modules.tc4 import AspectParser
from src.modules.tc4.shortest_path import ShortestPath
from src.modules.tc4.shortest_path2 import ShortestPath2

def test_construct():
    # setup aspects
    parser = AspectParser("src/modules/tc4/aspects.txt")
    aspects = parser.parse()
    for aspect in aspects.values():
        aspect.construct_neighbors(aspects)

    sp2 = ShortestPath2(list(aspects.values()))

    assert sp2
    assert sp2._aspects == list(aspects.values())
    assert sp2.graph == {}
    assert sp2.all_nodes == {}

def test_correct_path():
    # setup aspects
    parser = AspectParser("src/modules/tc4/aspects.txt")
    aspects = parser.parse()
    for aspect in aspects.values():
        aspect.construct_neighbors(aspects)

    sp = ShortestPath(list(aspects.values()))

    sp2 = ShortestPath2(list(aspects.values()))
    sp2.calculate_graph()

    path = sp.recursive(aspects["Motus"], aspects["Cognitio"])[0]
    path2 = sp2.recursive(sp2.all_nodes["Motus"], sp2.all_nodes["Cognitio"])
    assert len(path) == len(path2)

    path = sp.recursive(aspects["Ignis"], aspects["Nebrisum"])[0]
    path2 = sp2.recursive(sp2.all_nodes["Ignis"], sp2.all_nodes["Nebrisum"])
    assert len(path) == len(path2)

    path = sp.recursive(aspects["Telum"], aspects["Electrum"])[0]
    path2 = sp2.recursive(sp2.all_nodes["Telum"], sp2.all_nodes["Electrum"])
    assert len(path) == len(path2)
