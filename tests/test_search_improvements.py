"""Correctness, budgets and ordering checks for the optional optimizations."""

from collections import deque
import random
import pytest

from warehouse_mapf.cases import make_case
from warehouse_mapf.cbs import solve_cbs
from warehouse_mapf.grid import GridMap
from warehouse_mapf.metrics import sum_of_costs
from warehouse_mapf.models import Agent, EdgeConstraint, MAPFProblem, VertexConstraint
from warehouse_mapf.prioritized import solve_prioritized
from warehouse_mapf.search_support import DistanceCache, SearchStats, SearchTimeout
from warehouse_mapf.space_time_astar import space_time_astar
from warehouse_mapf.validation import validate_solution


def test_reverse_bfs_matches_independent_forward_bfs_on_random_grids():
    rng = random.Random(71)
    for _ in range(15):
        grid = GridMap(5, 6, frozenset((r, c) for r in range(5) for c in range(6)
                                     if (r, c) not in ((0, 0), (4, 5)) and rng.random() < 0.25))
        queue = deque([((0, 0), 0)])
        seen = {(0, 0)}
        expected = None
        while queue:
            pos, distance = queue.popleft()
            if pos == (4, 5):
                expected = distance
                break
            for nxt in grid.neighbors(pos):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, distance + 1))
        stats = SearchStats()
        cache = DistanceCache(grid, stats)
        assert cache.distances((4, 5)).get((0, 0)) == expected
        assert cache.distances((4, 5)).get((0, 0)) == expected
        assert stats.distance_cache_hits == 1
        paths = [space_time_astar(grid, (0, 0), (4, 5), heuristic=h) for h in ("manhattan", "static")]
        assert [(len(p) - 1) if p else None for p in paths] == [expected, expected]


@pytest.mark.parametrize("heuristic", ["manhattan", "static"])
def test_short_horizon_is_not_proof_of_impossibility(heuristic):
    problem = MAPFProblem(GridMap(1, 5), [Agent("A", (0, 0), (0, 4))])
    solution = solve_cbs(problem, max_time=2, heuristic=heuristic)
    assert solution.outcome == "no_solution_within_limits"
    blocked = MAPFProblem(GridMap(1, 5, frozenset({(0, 2)})), problem.agents)
    assert solve_cbs(blocked, heuristic=heuristic).outcome == "no_solution"


@pytest.mark.parametrize("heuristic", ["manhattan", "static"])
def test_heuristics_preserve_constraint_cost_and_goal_holding(heuristic):
    path = space_time_astar(GridMap(1, 3), (0, 0), (0, 2), heuristic=heuristic,
                            vertex_constraints=[VertexConstraint("A", 1, (0, 1))],
                            edge_constraints=[EdgeConstraint("A", 5, (0, 2), (0, 2))])
    assert path and len(path) - 1 == 6
    assert path[1] != (0, 1)
    problem = make_case("crossing")
    solution = solve_cbs(problem, heuristic=heuristic)
    assert validate_solution(problem, solution.paths).valid
    assert sum_of_costs(solution.paths) == 5
    assert solution.metadata["low_level_calls"] > 2
    if heuristic == "static":
        assert solution.metadata["distance_cache_hits"] > 0


def test_precomputation_obeys_deadline_and_does_not_cache_partial_tables():
    stats = SearchStats()
    cache = DistanceCache(GridMap(5, 5), stats)
    ticks = iter([0.0, 0.1, 0.2, 1.0])
    with pytest.raises(SearchTimeout):
        cache.distances((0, 0), deadline=0.5, clock=lambda: next(ticks))
    assert len(cache.distances((0, 0))) == 25
    assert stats.distance_cache_hits == 0
    problem = make_case("crossing")
    assert solve_cbs(problem, timeout_s=0, heuristic="static").timed_out
    assert solve_prioritized(problem, timeout_s=0, heuristic="static").timed_out


def test_priority_order_resolves_held_goal_counterexample():
    problem = make_case("goal_hold")
    assert not solve_prioritized(problem, max_time=20).success
    solution = solve_prioritized(problem, order="longest_first", max_time=20, heuristic="static")
    assert solution.success and validate_solution(problem, solution.paths).valid
    assert [a.id for a in problem.agents] == ["A", "B"]


def test_cases_have_valid_cbs_solutions():
    for name in ("corridor", "crossing", "goal_hold"):
        problem = make_case(name)
        solution = solve_cbs(problem, heuristic="static")
        assert solution.success and validate_solution(problem, solution.paths).valid
