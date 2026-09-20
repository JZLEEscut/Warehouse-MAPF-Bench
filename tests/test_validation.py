from warehouse_mapf.grid import GridMap
from warehouse_mapf.models import Agent, MAPFProblem
from warehouse_mapf.scenarios import make_warehouse_grid, sample_problem
from warehouse_mapf.validation import validate_solution


def test_validator_accepts_wait_and_rejects_jump():
    problem = MAPFProblem(GridMap(2, 3), [Agent("a", (0, 0), (0, 2)), Agent("b", (1, 0), (1, 2))])
    valid = {"a": [(0, 0), (0, 0), (0, 1), (0, 2)], "b": [(1, 0), (1, 1), (1, 2)]}
    assert validate_solution(problem, valid).valid
    assert not validate_solution(problem, {"a": [(0, 0), (0, 2)], "b": [(1, 0), (1, 2)]}).valid


def test_scenario_generator_is_deterministic():
    grid = make_warehouse_grid()
    first = sample_problem(grid, 8, 42)
    second = sample_problem(grid, 8, 42)
    assert first.agents == second.agents
    starts = [agent.start for agent in first.agents]
    goals = [agent.goal for agent in first.agents]
    assert len(set(starts)) == 8 and len(set(goals)) == 8
    assert all(grid.is_free(pos) for pos in starts + goals)
