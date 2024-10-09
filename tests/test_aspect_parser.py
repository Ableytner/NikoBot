# pylint: skip-file

from src.modules.tc4 import AspectParser

def test_create():
    parser = AspectParser("src/modules/tc4/aspects.txt")
    assert parser

def test_parse():
    parser = AspectParser("src/modules/tc4/aspects.txt")
    result = parser.parse()

    assert len(result) == 60
    for aspect_name, aspect in result.items():
        assert aspect_name == aspect.name
    
    telum = result["Telum"]
    assert telum
    assert telum.name == "Telum"
    assert not telum.primal()
    assert telum.keyword == "weapon"
    assert telum.component1.name == "Ignis" or telum.component1.name == "Instrumentum"
    assert telum.component2.name == "Ignis" or telum.component2.name == "Instrumentum"
    assert telum.neighbors is None

    ordo = result["Ordo"]
    assert ordo
    assert ordo.name == "Ordo"
    assert ordo.primal()
    assert ordo.keyword == "order"
    assert ordo.component1 is None
    assert ordo.component2 is None
    assert ordo.neighbors is None

def test_construct_neighbors():
    parser = AspectParser("src/modules/tc4/aspects.txt")
    result = parser.parse()

    assert len(result) == 60
    for aspect_name, aspect in result.items():
        assert aspect_name == aspect.name
    
    telum = result["Telum"]
    telum.construct_neighbors(result)

    assert len(telum.neighbors) == 3
    assert result["Ignis"] in telum.neighbors
    assert result["Instrumentum"] in telum.neighbors
    assert result["Ira"] in telum.neighbors

    ordo = result["Ordo"]
    ordo.construct_neighbors(result)

    assert len(ordo.neighbors) == 6
    assert result["Permutatio"] in ordo.neighbors
    assert result["Vitreus"] in ordo.neighbors
    assert result["Potentia"] in ordo.neighbors
    assert result["Motus"] in ordo.neighbors
    assert result["Sano"] in ordo.neighbors
    assert result["Instrumentum"] in ordo.neighbors
