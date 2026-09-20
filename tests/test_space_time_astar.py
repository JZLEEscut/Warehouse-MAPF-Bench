from warehouse_mapf.grid import GridMap
from warehouse_mapf.models import EdgeConstraint, VertexConstraint
from warehouse_mapf.space_time_astar import space_time_astar


def test_constraint_forces_wait():
    path = space_time_astar(GridMap(1, 3), (0, 0), (0, 2), vertex_constraints=[VertexConstraint("a", 1, (0, 1))], max_time=6)
    assert path == [(0, 0), (0, 0), (0, 1), (0, 2)]


def test_edge_and_future_goal_constraints():
    path = space_time_astar(GridMap(1, 3), (0, 0), (0, 2), edge_constraints=[EdgeConstraint("a", 0, (0, 0), (0, 1))], max_time=6)
    assert path and (path[0], path[1]) != ((0, 0), (0, 1))
    future = space_time_astar(GridMap(1, 2), (0, 0), (0, 1), vertex_constraints=[VertexConstraint("a", 3, (0, 1))], max_time=8)
    assert future and len(future) - 1 >= 4
