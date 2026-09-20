"""Reservation-based prioritized MAPF planning."""

from time import perf_counter
from .models import EdgeConstraint, MAPFProblem, Position, Solution, VertexConstraint
from .space_time_astar import space_time_astar
from .validation import validate_solution


def solve_prioritized(problem: MAPFProblem, *, max_time: int | None = None) -> Solution:
    """Plan in input order and reserve every earlier trajectory and held goal."""
    started = perf_counter()
    horizon = max_time if max_time is not None else problem.grid.height * problem.grid.width + 10
    paths: dict[str, list[Position]] = {}
    for agent in problem.agents:
        vertices: list[VertexConstraint] = []
        edges: list[EdgeConstraint] = []
        for prior_path in paths.values():
            for time in range(horizon + 1):
                vertices.append(VertexConstraint(agent.id, time, prior_path[min(time, len(prior_path) - 1)]))
            for time in range(min(horizon, len(prior_path) - 1)):
                source, target = prior_path[time], prior_path[time + 1]
                edges.append(EdgeConstraint(agent.id, time, target, source))
        path = space_time_astar(problem.grid, agent.start, agent.goal, vertex_constraints=vertices, edge_constraints=edges, max_time=horizon)
        if path is None:
            return Solution(paths, False, (perf_counter() - started) * 1000, {"failure_reason": f"no reserved path for {agent.id}"})
        paths[agent.id] = path
    validation = validate_solution(problem, paths)
    result = Solution(paths, validation.valid, (perf_counter() - started) * 1000, {"valid": validation.valid, "conflicts": len(validation.conflicts)})
    if not validation.valid:
        result.metadata["failure_reason"] = "; ".join(validation.errors)
    return result
