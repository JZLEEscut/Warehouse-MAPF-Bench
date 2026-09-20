from warehouse_mapf.astar import astar
from warehouse_mapf.grid import GridMap


def test_astar_shortest_and_detour():
    assert len(astar(GridMap(3, 4), (0, 0), (2, 3))) - 1 == 5
    path = astar(GridMap(3, 3, frozenset({(0, 1)})), (0, 0), (0, 2))
    assert path is not None and (0, 1) not in path and len(path) - 1 == 4


def test_astar_equal_and_unreachable():
    grid = GridMap(3, 3, frozenset({(0, 1), (1, 0), (1, 2), (2, 1)}))
    assert astar(grid, (1, 1), (1, 1)) == [(1, 1)]
    assert astar(grid, (1, 1), (0, 0)) is None
