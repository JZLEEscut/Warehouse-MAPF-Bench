"""Paired deterministic benchmark runner."""

import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from .astar import solve_independent
from .cbs import solve_cbs
from .metrics import count_conflicts, makespan, sum_of_costs
from .prioritized import solve_prioritized
from .scenarios import make_warehouse_grid, sample_problem
from .validation import validate_solution

RESULT_COLUMNS = ["algorithm", "seed", "num_agents", "success", "valid", "runtime_ms", "sum_of_costs", "makespan", "conflicts", "failure_reason", "expanded_nodes"]


def _record(name: str, seed: int, count: int, problem, solution) -> dict[str, object]:
    validation = validate_solution(problem, solution.paths) if solution.paths else None
    valid = bool(solution.success and validation and validation.valid)
    return {
        "algorithm": name, "seed": seed, "num_agents": count,
        "success": solution.success, "valid": valid,
        "runtime_ms": round(solution.runtime_ms, 3),
        "sum_of_costs": sum_of_costs(solution.paths) if solution.success else None,
        "makespan": makespan(solution.paths) if solution.success else None,
        "conflicts": count_conflicts(solution.paths) if solution.paths else 0,
        "failure_reason": solution.metadata.get("failure_reason", ""),
        "expanded_nodes": solution.metadata.get("expanded_nodes", 0),
    }


def _summarize(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (algorithm, count), group in frame.groupby(["algorithm", "num_agents"], sort=True):
        valid = group[group["valid"]]
        records.append({
            "algorithm": algorithm, "num_agents": count, "runs": len(group),
            "success_rate": round(float(group["success"].mean()), 3),
            "valid_rate": round(float(group["valid"].mean()), 3),
            "median_runtime_ms": round(float(group["runtime_ms"].median()), 3),
            "mean_runtime_ms": round(float(group["runtime_ms"].mean()), 3),
            "median_sum_of_costs_solved": round(float(valid["sum_of_costs"].median()), 3) if not valid.empty else None,
            "median_makespan_solved": round(float(valid["makespan"].median()), 3) if not valid.empty else None,
            "mean_conflicts": round(float(group["conflicts"].mean()), 3),
        })
    return pd.DataFrame(records)


def _plots(summary: pd.DataFrame) -> None:
    destination = Path("assets")
    destination.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    for name, group in summary.groupby("algorithm", sort=True):
        ax.plot(group["num_agents"], group["median_runtime_ms"], marker="o", label=name)
    ax.set(title="Median runtime across paired quick runs", xlabel="Number of agents", ylabel="Runtime (ms)")
    ax.legend()
    fig.savefig(destination / "runtime_vs_agents.png", dpi=160)
    plt.close(fig)
    feasible = summary[summary["algorithm"] != "independent_astar"].dropna(subset=["median_sum_of_costs_solved"])
    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    for name, group in feasible.groupby("algorithm", sort=True):
        ax.plot(group["num_agents"], group["median_sum_of_costs_solved"], marker="o", label=name)
    ax.set(title="Median sum of costs on valid solved runs", xlabel="Number of agents", ylabel="Sum of costs")
    ax.legend()
    fig.savefig(destination / "cost_vs_agents.png", dpi=160)
    plt.close(fig)


def run_benchmark(*, quick: bool = False, counts: list[int] | None = None, seeds: int | None = None, cbs_timeout: float | None = None) -> pd.DataFrame:
    """Run all algorithms on the same instance for every count/seed pair."""
    counts = counts or ([5, 10, 15] if quick else [5, 10, 15, 20])
    seed_count = seeds if seeds is not None else (5 if quick else 10)
    timeout = cbs_timeout if cbs_timeout is not None else (0.6 if quick else 2.0)
    grid = make_warehouse_grid()
    records = []
    for count in counts:
        for seed in range(seed_count):
            problem = sample_problem(grid, count, seed)
            records.append(_record("independent_astar", seed, count, problem, solve_independent(problem)))
            records.append(_record("prioritized", seed, count, problem, solve_prioritized(problem)))
            records.append(_record("cbs", seed, count, problem, solve_cbs(problem, timeout_s=timeout, max_expansions=5000)))
    results = pd.DataFrame(records, columns=RESULT_COLUMNS)
    Path("benchmarks").mkdir(exist_ok=True)
    results.to_csv("benchmarks/results.csv", index=False)
    summary = _summarize(results)
    summary.to_csv("benchmarks/summary.csv", index=False)
    _plots(summary)
    print(f"wrote {len(results)} measured runs to benchmarks/results.csv")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--agents", nargs="+", type=int)
    parser.add_argument("--seeds", type=int)
    parser.add_argument("--cbs-timeout", type=float)
    args = parser.parse_args()
    run_benchmark(quick=args.quick, counts=args.agents, seeds=args.seeds, cbs_timeout=args.cbs_timeout)


if __name__ == "__main__":
    main()
