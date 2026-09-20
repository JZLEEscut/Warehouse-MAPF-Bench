"""Standard two-level Conflict-Based Search."""

from dataclasses import dataclass, field
from heapq import heappop, heappush
from itertools import count
from time import perf_counter
from .conflicts import Conflict, find_first_conflict
from .metrics import sum_of_costs
from .models import EdgeConstraint, MAPFProblem, Position, Solution, VertexConstraint
from .space_time_astar import space_time_astar
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


def solve_cbs(problem: MAPFProblem, *, timeout_s: float = 3.0, max_expansions: int = 10_000, max_time: int | None = None) -> Solution:
    """Branch on the earliest conflict and replan only the constrained agent."""
    started = perf_counter()
    horizon = max_time if max_time is not None else problem.grid.height * problem.grid.width + 10
    root_paths: dict[str, list[Position]] = {}
    for agent in problem.agents:
        path = space_time_astar(problem.grid, agent.start, agent.goal, max_time=horizon)
        if path is None:
            return Solution({}, False, (perf_counter() - started) * 1000, {"failure_reason": f"unreachable:{agent.id}"})
        root_paths[agent.id] = path
    tickets = count()
    queue = [CBSNode(sum_of_costs(root_paths), next(tickets), (), root_paths)]
    seen = {_signature(())}
    by_id = {agent.id: agent for agent in problem.agents}
    expanded = 0
    while queue:
        elapsed = perf_counter() - started
        if elapsed > timeout_s:
            return Solution({}, False, elapsed * 1000, {"failure_reason": "timeout", "expanded_nodes": expanded})
        if expanded >= max_expansions:
            return Solution({}, False, elapsed * 1000, {"failure_reason": "expansion_limit", "expanded_nodes": expanded})
        node = heappop(queue)
        expanded += 1
        conflict = find_first_conflict(node.paths)
        if conflict is None:
            validation = validate_solution(problem, node.paths)
            return Solution(node.paths, validation.valid, (perf_counter() - started) * 1000, {"valid": validation.valid, "conflicts": len(validation.conflicts), "expanded_nodes": expanded})
        for constraint in _split(conflict):
            constraints = node.constraints + (constraint,)
            signature = _signature(constraints)
            if signature in seen:
                continue
            seen.add(signature)
            agent = by_id[constraint.agent]
            vertices = [item for item in constraints if isinstance(item, VertexConstraint) and item.agent == agent.id]
            edges = [item for item in constraints if isinstance(item, EdgeConstraint) and item.agent == agent.id]
            path = space_time_astar(problem.grid, agent.start, agent.goal, vertex_constraints=vertices, edge_constraints=edges, max_time=horizon)
            if path is None:
                continue
            child_paths = dict(node.paths)
            child_paths[agent.id] = path
            heappush(queue, CBSNode(sum_of_costs(child_paths), next(tickets), constraints, child_paths))
    return Solution({}, False, (perf_counter() - started) * 1000, {"failure_reason": "search_exhausted", "expanded_nodes": expanded})
