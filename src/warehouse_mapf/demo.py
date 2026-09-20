"""Generate a deterministic conflict-free warehouse GIF."""

import argparse
from pathlib import Path
from .cbs import solve_cbs
from .metrics import makespan, sum_of_costs
from .prioritized import solve_prioritized
from .scenarios import make_warehouse_grid, sample_problem
from .validation import validate_solution
from .visualization import save_animation


def run_demo(*, solver: str = "prioritized", agents: int = 8, seed: int = 17, output: str | Path = "assets/demo.gif") -> Path:
    """Solve and render a fixed synthetic warehouse scenario."""
    problem = sample_problem(make_warehouse_grid(), agents, seed)
    solution = solve_prioritized(problem) if solver == "prioritized" else solve_cbs(problem, timeout_s=8)
    if not solution.success:
        raise RuntimeError(f"demo failed: {solution.metadata.get('failure_reason')}")
    validation = validate_solution(problem, solution.paths)
    if not validation.valid:
        raise RuntimeError(f"invalid demo: {validation.errors}")
    artifact = save_animation(problem, solution.paths, output)
    print(f"saved {artifact} | solver={solver} | agents={agents} | cost={sum_of_costs(solution.paths)} | makespan={makespan(solution.paths)}")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", choices=("prioritized", "cbs"), default="prioritized")
    parser.add_argument("--agents", type=int, default=8)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", default="assets/demo.gif")
    args = parser.parse_args()
    run_demo(solver=args.solver, agents=args.agents, seed=args.seed, output=args.output)


if __name__ == "__main__":
    main()
