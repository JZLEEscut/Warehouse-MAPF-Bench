from warehouse_mapf.grid import GridMap
from warehouse_mapf.models import Agent, MAPFProblem
from warehouse_mapf.prioritized import solve_prioritized
from warehouse_mapf.validation import validate_solution


def test_prioritized_crossing_is_valid():
    problem = MAPFProblem(GridMap(3, 3), [Agent("a", (1, 0), (1, 2)), Agent("b", (0, 1), (2, 1))])
    solution = solve_prioritized(problem)
    assert solution.success and validate_solution(problem, solution.paths).valid
