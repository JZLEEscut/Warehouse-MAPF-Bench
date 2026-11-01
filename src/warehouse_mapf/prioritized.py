"""Reservation-based prioritized MAPF planning."""

from time import perf_counter
from .models import EdgeConstraint, MAPFProblem, Position, Solution, VertexConstraint
from .space_time_astar import space_time_astar
from .validation import validate_solution
from .search_support import DistanceCache, Heuristic, SearchStats, SearchTimeout


def solve_prioritized(problem: MAPFProblem, *, max_time: int | None = None,
                      heuristic: Heuristic = "manhattan", order: str = "input",
                      timeout_s: float | None = None) -> Solution:
    """Plan in input order and reserve every earlier trajectory and held goal."""
    started = perf_counter()
    deadline = None if timeout_s is None else started + max(0.0, timeout_s)
    stats = SearchStats()
    cache = DistanceCache(problem.grid, stats)
    if order not in ("input", "longest_first"):
        raise ValueError(f"unknown priority order: {order}")
    agents = list(problem.agents)
    paths: dict[str, list[Position]] = {}

    def finish(success: bool, outcome: str, reason: str = "") -> Solution:
        validation = validate_solution(problem, paths) if success else None
        return Solution(paths=dict(paths), success=success, outcome=outcome,
                        timed_out=outcome == "timeout", runtime_ms=(perf_counter() - started) * 1000,
                        metadata={**stats.metadata(), "heuristic": heuristic, "priority_order": order,
                                  "failure_reason": reason, "valid": bool(validation and validation.valid),
                                  "conflicts": len(validation.conflicts) if validation else 0})

    if order == "longest_first":
        try:
            distances = {a.id: cache.distances(a.goal, deadline=deadline).get(a.start, -1) for a in agents}
        except SearchTimeout:
            return finish(False, "timeout", "timeout")
        agents.sort(key=lambda a: -distances[a.id])  # stable ties retain input order
    horizon = max_time if max_time is not None else problem.grid.height * problem.grid.width + 10
    for agent in agents:
        vertices: list[VertexConstraint] = []
        edges: list[EdgeConstraint] = []
        for prior_path in paths.values():
            for time in range(horizon + 1):
                if deadline is not None and perf_counter() >= deadline:
                    return finish(False, "timeout", "timeout")
                vertices.append(VertexConstraint(agent.id, time, prior_path[min(time, len(prior_path) - 1)]))
            for time in range(min(horizon, len(prior_path) - 1)):
                source, target = prior_path[time], prior_path[time + 1]
                edges.append(EdgeConstraint(agent.id, time, target, source))
        try:
            path = space_time_astar(problem.grid, agent.start, agent.goal, vertex_constraints=vertices,
                                    edge_constraints=edges, max_time=horizon, heuristic=heuristic,
                                    distance_cache=cache, stats=stats, deadline=deadline)
        except SearchTimeout:
            return finish(False, "timeout", "timeout")
        if path is None:
            return finish(False, "no_solution_within_limits", f"no reserved path for {agent.id}")
        paths[agent.id] = path
    return finish(True, "solved")
