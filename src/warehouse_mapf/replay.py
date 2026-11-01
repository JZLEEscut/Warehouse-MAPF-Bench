"""One independently checked payload shared by live and recorded replays."""

from dataclasses import asdict

from .conflicts import find_all_conflicts
from .metrics import makespan, sum_of_costs
from .models import MAPFProblem, Solution
from .validation import validate_solution


def replay_payload(problem: MAPFProblem, solution: Solution) -> dict:
    validation = validate_solution(problem, solution.paths) if solution.success else None
    return {
        "grid": {"height": problem.grid.height, "width": problem.grid.width,
                 "obstacles": sorted(problem.grid.obstacles)},
        "agents": [asdict(agent) for agent in problem.agents],
        "paths": solution.paths, "outcome": solution.outcome,
        "success": solution.success, "timed_out": solution.timed_out,
        "valid": bool(validation and validation.valid),
        "validation_errors": validation.errors if validation else [],
        "runtime_ms": solution.runtime_ms,
        "sum_of_costs": sum_of_costs(solution.paths) if solution.success else None,
        "makespan": makespan(solution.paths) if solution.success else None,
        "replay_steps": max((len(p) - 1 for p in solution.paths.values()), default=0),
        "conflicts": [asdict(c) for c in find_all_conflicts(solution.paths)] if solution.paths else [],
        "metadata": solution.metadata,
    }
