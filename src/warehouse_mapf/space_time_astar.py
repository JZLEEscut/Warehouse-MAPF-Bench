"""Constrained A* on (position, time), including WAIT."""

from collections.abc import Collection
from heapq import heappop, heappush
from itertools import count
from time import perf_counter
from typing import Callable
from .astar import manhattan
from .grid import GridMap
from .models import EdgeConstraint, Position, VertexConstraint
from .search_support import DistanceCache, Heuristic, SearchStats, SearchTimeout


def space_time_astar(
    grid: GridMap,
    start: Position,
    goal: Position,
    *,
    vertex_constraints: Collection[VertexConstraint] = (),
    edge_constraints: Collection[EdgeConstraint] = (),
    max_time: int | None = None,
    deadline: float | None = None,
    clock: Callable[[], float] = perf_counter,
    heuristic: Heuristic = "manhattan",
    distance_cache: DistanceCache | None = None,
    stats: SearchStats | None = None,
) -> list[Position] | None:
    """Find a constrained path; edge constraints at t forbid t->t+1 moves."""
    if heuristic not in ("manhattan", "static"):
        raise ValueError(f"unknown heuristic: {heuristic}")
    stats = stats if stats is not None else SearchStats()
    stats.low_level_calls += 1
    if not grid.is_free(start) or not grid.is_free(goal):
        return None
    table = None
    if heuristic == "static":
        cache = distance_cache if distance_cache is not None else DistanceCache(grid, stats)
        if cache.grid != grid:
            raise ValueError("distance cache belongs to a different grid")
        table = cache.distances(goal, deadline=deadline, clock=clock)
        if start not in table:
            return None

    def estimate(position: Position) -> int:
        return table[position] if table is not None else manhattan(position, goal)
    blocked_vertices = {(item.time, item.position) for item in vertex_constraints}
    blocked_edges = {(item.time, item.source, item.target) for item in edge_constraints}
    if (0, start) in blocked_vertices:
        return None
    latest = max((item.time for item in (*vertex_constraints, *edge_constraints)), default=0)
    latest_goal = max((item.time for item in vertex_constraints if item.position == goal), default=0)
    latest_goal = max(latest_goal, max((item.time + 1 for item in edge_constraints
                                     if item.source == goal and item.target == goal), default=0))
    horizon = max_time if max_time is not None else grid.height * grid.width + latest + 10
    ticket = count()
    queue: list[tuple[int, int, int, Position, int]] = [(estimate(start), 0, next(ticket), start, 0)]
    start_state = (start, 0)
    parents: dict[tuple[Position, int], tuple[Position, int] | None] = {start_state: None}
    best = {start_state: 0}
    while queue:
        if deadline is not None and clock() >= deadline:
            raise SearchTimeout("space-time search deadline exceeded")
        _, cost, _, position, time = heappop(queue)
        state = (position, time)
        if cost != best.get(state):
            continue
        stats.low_level_expanded += 1
        if position == goal and time >= latest_goal:
            path = [position]
            current = state
            while parents[current] is not None:
                current = parents[current]  # type: ignore[assignment]
                path.append(current[0])
            return list(reversed(path))
        if time >= horizon:
            continue
        for nxt in grid.neighbors(position, include_wait=True):
            next_time = time + 1
            if (next_time, nxt) in blocked_vertices or (time, position, nxt) in blocked_edges:
                continue
            next_state = (nxt, next_time)
            new_cost = cost + 1
            if new_cost < best.get(next_state, float("inf")):
                best[next_state] = new_cost
                parents[next_state] = state
                heappush(queue, (new_cost + estimate(nxt), new_cost, next(ticket), nxt, next_time))
    return None
