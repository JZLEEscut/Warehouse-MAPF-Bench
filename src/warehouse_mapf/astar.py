"""Static A* and the conflict-unaware multi-agent baseline."""

from heapq import heappop, heappush
from itertools import count
from time import perf_counter
from .grid import GridMap
from .models import MAPFProblem, Position, Solution
from .validation import validate_solution


def manhattan(a: Position, b: Position) -> int:
    """Return Manhattan distance."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: GridMap, start: Position, goal: Position) -> list[Position] | None:
    """Find a shortest static 4-neighbour path, or None."""
    if not grid.is_free(start) or not grid.is_free(goal):
        return None
    queue: list[tuple[int, int, int, Position]] = []
    ticket = count()
    heappush(queue, (manhattan(start, goal), 0, next(ticket), start))
    parents: dict[Position, Position | None] = {start: None}
    best = {start: 0}
    while queue:
        _, cost, _, current = heappop(queue)
        if cost != best.get(current):
            continue
        if current == goal:
            path = [current]
            while parents[path[-1]] is not None:
                path.append(parents[path[-1]])  # type: ignore[arg-type]
            return list(reversed(path))
        for nxt in grid.neighbors(current):
            new_cost = cost + 1
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                parents[nxt] = current
                heappush(queue, (new_cost + manhattan(nxt, goal), new_cost, next(ticket), nxt))
    return None


def solve_independent(problem: MAPFProblem) -> Solution:
    """Plan each agent independently, allowing inter-agent conflicts."""
    started = perf_counter()
    paths: dict[str, list[Position]] = {}
    for agent in problem.agents:
        path = astar(problem.grid, agent.start, agent.goal)
        if path is None:
            return Solution(paths, False, (perf_counter() - started) * 1000, {"failure_reason": f"unreachable:{agent.id}"})
        paths[agent.id] = path
    validation = validate_solution(problem, paths)
    return Solution(paths, True, (perf_counter() - started) * 1000, {"valid": validation.valid, "conflicts": len(validation.conflicts)})
