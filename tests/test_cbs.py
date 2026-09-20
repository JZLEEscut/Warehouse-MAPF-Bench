from warehouse_mapf.cbs import solve_cbs
from warehouse_mapf.grid import GridMap
from warehouse_mapf.metrics import sum_of_costs
from warehouse_mapf.models import Agent, MAPFProblem
from warehouse_mapf.validation import validate_solution


def test_cbs_vertex_crossing():
    problem = MAPFProblem(GridMap(3, 3), [Agent("a", (1, 0), (1, 2)), Agent("b", (0, 1), (2, 1))])
    solution = solve_cbs(problem, timeout_s=2)
    assert solution.success and validate_solution(problem, solution.paths).valid
    assert sum_of_costs(solution.paths) == 5


def test_cbs_edge_swap_with_alternate_route():
    problem = MAPFProblem(GridMap(2, 3), [Agent("a", (0, 0), (0, 1)), Agent("b", (0, 1), (0, 0))])
    solution = solve_cbs(problem, timeout_s=2)
    assert solution.success and validate_solution(problem, solution.paths).valid


def test_cbs_resolves_cascading_three_agent_conflicts():
    problem = MAPFProblem(GridMap(3, 3), [
        Agent("a", (1, 0), (1, 2)),
        Agent("b", (0, 1), (2, 1)),
        Agent("c", (1, 2), (1, 0)),
    ])
    solution = solve_cbs(problem, timeout_s=3)
    assert solution.success
    assert validate_solution(problem, solution.paths).valid
    assert solution.metadata["expanded_nodes"] > 2


def test_cbs_impossible_static_case_has_clean_outcome():
    problem = MAPFProblem(GridMap(1, 3, frozenset({(0, 1)})), [Agent("a", (0, 0), (0, 2))])
    solution = solve_cbs(problem, timeout_s=2)
    assert not solution.success
    assert not solution.timed_out
    assert solution.outcome == "no_solution"


def test_cbs_timeout_is_deterministic_with_injected_clock():
    class StepClock:
        def __init__(self):
            self.value = 0.0

        def __call__(self):
            self.value += 0.01
            return self.value

    problem = MAPFProblem(GridMap(3, 3), [Agent("a", (1, 0), (1, 2)), Agent("b", (0, 1), (2, 1))])
    solution = solve_cbs(problem, timeout_s=0.005, clock=StepClock())
    assert solution.outcome == "timeout"
    assert solution.timed_out
    assert not solution.success
