from warehouse_mapf.conflicts import find_all_conflicts, find_first_conflict, position_at


def test_vertex_and_edge_conflicts():
    vertex = find_first_conflict({"a": [(0, 0), (0, 1), (0, 2)], "b": [(0, 2), (0, 1), (0, 0)]})
    assert vertex and vertex.kind == "vertex" and vertex.time == 1
    edge = find_all_conflicts({"a": [(0, 0), (0, 1)], "b": [(0, 1), (0, 0)]})
    assert len(edge) == 1 and edge[0].kind == "edge"


def test_goal_holding_with_unequal_paths():
    paths = {"a": [(0, 0)], "b": [(0, 1), (0, 0)]}
    assert position_at(paths["a"], 10) == (0, 0)
    assert find_first_conflict(paths).time == 1
