"""Standard two-level Conflict-Based Search."""

from dataclasses import dataclass, field
from heapq import heappop, heappush
from itertools import count
from time import perf_counter
from typing import Callable
from .conflicts import Conflict, find_first_conflict
from .metrics import sum_of_costs
from .models import EdgeConstraint, MAPFProblem, Position, Solution, VertexConstraint
from .space_time_astar import SearchTimeout, space_time_astar
from .validation import validate_solution

Constraint = VertexConstraint | EdgeConstraint


@dataclass(order=True)
class CBSNode:
    """Constraint-tree node ordered only by path cost and a stable ticket."""
    cost: int
    ticket: int
    constraints: tuple[Constraint, ...] = field(compare=False)
    paths: dict[str, list[Position]] = field(compare=False)


def _signature(constraints: tuple[Constraint, ...]) -> tuple[str, ...]:
    return tuple(sorted(map(repr, constraints)))


def _split(conflict: Conflict) -> tuple[Constraint, Constraint]:
    if conflict.kind == "vertex":
        assert conflict.position is not None
        return (VertexConstraint(conflict.agent1, conflict.time, conflict.position), VertexConstraint(conflict.agent2, conflict.time, conflict.position))
    assert conflict.edge1 is not None and conflict.edge2 is not None
    return (EdgeConstraint(conflict.agent1, conflict.time, *conflict.edge1), EdgeConstraint(conflict.agent2, conflict.time, *conflict.edge2))


def solve_cbs(
    problem: MAPFProblem,
    *,
    timeout_s: float = 3.0,
    max_expansions: int = 10_000,
    max_time: int | None = None,
    clock: Callable[[], float] = perf_counter,
) -> Solution:
    """Branch on conflicts while sharing one deadline with low-level searches."""
    started = clock()
    deadline = started + max(0.0, timeout_s)
    horizon = max_time if max_time is not None else problem.grid.height * problem.grid.width + 10
    root_paths: dict[str, list[Position]] = {}
    try:
        for agent in problem.agents:
            path = space_time_astar(
                problem.grid,
                agent.start,
                agent.goal,
                max_time=horizon,
                deadline=deadline,
                clock=clock,
            )
            if path is None:
                return Solution(
                    paths={},
                    success=False,
                    runtime_ms=(clock() - started) * 1000,
                    metadata={"failure_reason": f"unreachable:{agent.id}"},
                    outcome="no_solution",
                )
            root_paths[agent.id] = path
    except SearchTimeout:
        return Solution(
            paths={},
            success=False,
            runtime_ms=max(0.0, (clock() - started) * 1000),
            metadata={"failure_reason": "timeout", "expanded_nodes": 0},
            outcome="timeout",
            timed_out=True,
        )
    tickets = count()
    queue = [CBSNode(sum_of_costs(root_paths), next(tickets), (), root_paths)]
    seen = {_signature(())}
    by_id = {agent.id: agent for agent in problem.agents}
    expanded = 0
    while queue:
        elapsed = clock() - started
        if clock() >= deadline:
            return Solution(
                paths={}, success=False, runtime_ms=max(0.0, elapsed * 1000),
                metadata={"failure_reason": "timeout", "expanded_nodes": expanded},
                outcome="timeout", timed_out=True,
            )
        if expanded >= max_expansions:
            return Solution(
                paths={}, success=False, runtime_ms=max(0.0, elapsed * 1000),
                metadata={"failure_reason": "expansion_limit", "expanded_nodes": expanded},
                outcome="no_solution_within_limits",
            )
        node = heappop(queue)
        expanded += 1
        conflict = find_first_conflict(node.paths)
        if conflict is None:
            validation = validate_solution(problem, node.paths)
            return Solution(
                paths=node.paths,
                success=True,
                runtime_ms=max(0.0, (clock() - started) * 1000),
                metadata={
                    "valid": validation.valid,
                    "conflicts": len(validation.conflicts),
                    "validation_error": "; ".join(validation.errors),
                    "expanded_nodes": expanded,
                },
                outcome="solved",
            )
        for constraint in _split(conflict):
            constraints = node.constraints + (constraint,)
            signature = _signature(constraints)
            if signature in seen:
                continue
            seen.add(signature)
            agent = by_id[constraint.agent]
            vertices = [item for item in constraints if isinstance(item, VertexConstraint) and item.agent == agent.id]
            edges = [item for item in constraints if isinstance(item, EdgeConstraint) and item.agent == agent.id]
            try:
                path = space_time_astar(
                    problem.grid,
                    agent.start,
                    agent.goal,
                    vertex_constraints=vertices,
                    edge_constraints=edges,
                    max_time=horizon,
                    deadline=deadline,
                    clock=clock,
                )
            except SearchTimeout:
                return Solution(
                    paths={}, success=False, runtime_ms=max(0.0, (clock() - started) * 1000),
                    metadata={"failure_reason": "timeout", "expanded_nodes": expanded},
                    outcome="timeout", timed_out=True,
                )
            if path is None:
                continue
            child_paths = dict(node.paths)
            child_paths[agent.id] = path
            heappush(queue, CBSNode(sum_of_costs(child_paths), next(tickets), constraints, child_paths))
    return Solution(
        paths={}, success=False, runtime_ms=max(0.0, (clock() - started) * 1000),
        metadata={"failure_reason": "search_exhausted", "expanded_nodes": expanded},
        outcome="no_solution_within_limits",
    )
