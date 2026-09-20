"""Independent solver-output validation."""

from dataclasses import dataclass
from .conflicts import Conflict, find_all_conflicts
from .models import MAPFProblem, Position


@dataclass
class ValidationResult:
    """Validity status plus diagnostic errors and conflicts."""
    valid: bool
    errors: list[str]
    conflicts: list[Conflict]


def _legal_step(a: Position, b: Position) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) in (0, 1)


def validate_solution(problem: MAPFProblem, paths: dict[str, list[Position]]) -> ValidationResult:
    """Validate IDs, endpoints, motion, cells, vertex conflicts, and edge swaps."""
    errors: list[str] = []
    if set(paths) != {agent.id for agent in problem.agents}:
        errors.append("path agent IDs do not match problem agents")
    for agent in problem.agents:
        path = paths.get(agent.id)
        if not path:
            errors.append(f"{agent.id}: missing path")
            continue
        if path[0] != agent.start:
            errors.append(f"{agent.id}: wrong start")
        if path[-1] != agent.goal:
            errors.append(f"{agent.id}: wrong goal")
        if any(not problem.grid.is_free(pos) for pos in path):
            errors.append(f"{agent.id}: obstacle or out-of-bounds cell")
        if any(not _legal_step(a, b) for a, b in zip(path, path[1:])):
            errors.append(f"{agent.id}: illegal jump")
    complete = {key: value for key, value in paths.items() if value}
    conflicts = find_all_conflicts(complete) if len(complete) > 1 else []
    if conflicts:
        errors.append(f"detected {len(conflicts)} conflicts")
    return ValidationResult(not errors, errors, conflicts)
