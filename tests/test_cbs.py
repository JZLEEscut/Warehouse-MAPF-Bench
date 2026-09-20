from warehouse_mapf.cbs import solve_cbs
from warehouse_mapf.grid import GridMap
from warehouse_mapf.models import Agent, MAPFProblem
from warehouse_mapf.validation import validate_solution


def test_cbs_vertex_crossing():
    problem = MAPFProblem(GridMap(3, 3), [Agent("a", (1, 0), (1, 2)), Agent("b", (0, 1), (2, 1))])
    solution = solve_cbs(problem, timeout_s=2)
    assert solution.success and validate_solution(problem, solution.paths).valid


def test_cbs_edge_swap_with_alternate_route():
    problem = MAPFProblem(GridMap(2, 3), [Agent("a", (0, 0), (0, 1)), Agent("b", (0, 1), (0, 0))])
    solution = solve_cbs(problem, timeout_s=2)
    assert solution.success and validate_solution(problem, solution.paths).valid
