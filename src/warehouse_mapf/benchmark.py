"""Deterministic synthetic benchmark runner with paired-valid reporting."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .astar import solve_independent
from .cbs import solve_cbs
from .metrics import count_conflicts, makespan, sum_of_costs
from .models import MAPFProblem, Solution
from .prioritized import solve_prioritized
from .reporting import paired_valid_details, summarize_paired, summarize_runs
from .scenarios import make_warehouse_grid, sample_problem
from .validation import validate_solution

RUN_COLUMNS = [
    "source", "map_id", "scenario_id", "selection_row_ids", "instance_id",
    "algorithm", "seed", "num_agents", "outcome", "success", "valid", "timed_out",
    "runtime_ms", "sum_of_costs", "makespan", "conflicts", "validation_error",
    "failure_reason", "expanded_nodes", "limit_seconds",
]


@dataclass(frozen=True)
class BenchmarkInstance:
    """A MAPF problem plus immutable identity and provenance for pairing."""
    problem: MAPFProblem
    source: str
    map_id: str
    scenario_id: str
    instance_id: str
    seed: int
    selection_row_ids: str = "-"


def synthetic_instances(counts: list[int], seeds: int) -> list[BenchmarkInstance]:
    """Create deterministic synthetic instances."""
    grid = make_warehouse_grid()
    result = []
    for count in counts:
        for seed in range(seeds):
            instance_id = f"synthetic-18x28:n{count}:seed{seed}"
            result.append(BenchmarkInstance(
                sample_problem(grid, count, seed), "synthetic", "synthetic-warehouse-18x28",
                f"seed-{seed}", instance_id, seed,
            ))
    return result


def _safe_solve(name: str, problem: MAPFProblem, cbs_timeout: float) -> Solution:
    started = perf_counter()
    try:
        if name == "independent_astar":
            return solve_independent(problem)
        if name == "prioritized":
            return solve_prioritized(problem)
        if name == "cbs":
            return solve_cbs(problem, timeout_s=cbs_timeout, max_expansions=10_000)
        raise ValueError(f"unknown algorithm: {name}")
    except Exception as exc:
        return Solution(paths={}, success=False, runtime_ms=(perf_counter() - started) * 1000,
                        metadata={"failure_reason": f"{type(exc).__name__}: {exc}"}, outcome="error")


def record_run(instance: BenchmarkInstance, algorithm: str, solution: Solution, limit_seconds: float) -> dict[str, object]:
    """Validate a returned solution while preserving its original outcome."""
    validation = validate_solution(instance.problem, solution.paths) if solution.success else None
    valid = bool(solution.success and validation and validation.valid)
    return {
        "source": instance.source, "map_id": instance.map_id, "scenario_id": instance.scenario_id,
        "selection_row_ids": instance.selection_row_ids, "instance_id": instance.instance_id,
        "algorithm": algorithm, "seed": instance.seed, "num_agents": len(instance.problem.agents),
        "outcome": solution.outcome, "success": solution.success, "valid": valid,
        "timed_out": solution.timed_out, "runtime_ms": round(max(0.0, solution.runtime_ms), 3),
        "sum_of_costs": sum_of_costs(solution.paths) if solution.success else None,
        "makespan": makespan(solution.paths) if solution.success else None,
        "conflicts": count_conflicts(solution.paths) if solution.paths else 0,
        "validation_error": "; ".join(validation.errors) if validation and not validation.valid else "",
        "failure_reason": solution.metadata.get("failure_reason", ""),
        "expanded_nodes": solution.metadata.get("expanded_nodes", 0),
        "limit_seconds": limit_seconds if algorithm == "cbs" else None,
    }


def _plot_outputs(summary: pd.DataFrame, paired: pd.DataFrame, asset_dir: Path, prefix: str) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    combined = summary.groupby(["algorithm", "num_agents"], as_index=False).agg(
        median_runtime_ms_all_attempts=("median_runtime_ms_all_attempts", "median"),
        valid_rate=("valid_rate", "mean"),
    )
    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    for name, group in combined.groupby("algorithm", sort=True):
        ax.plot(group["num_agents"], group["median_runtime_ms_all_attempts"], marker="o", label=name)
    ax.set(title="Median runtime — all attempted instances", xlabel="Number of agents", ylabel="Runtime (ms)")
    ax.legend()
    fig.savefig(asset_dir / f"{prefix}runtime_all_attempts.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    width = 0.12
    counts = sorted(combined["num_agents"].unique())
    algorithms = sorted(combined["algorithm"].unique())
    for index, name in enumerate(algorithms):
        group = combined[combined["algorithm"] == name].set_index("num_agents")
        x = [value + (index - (len(algorithms) - 1) / 2) * width for value in counts]
        ax.bar(x, [group.loc[value, "valid_rate"] if value in group.index else 0 for value in counts], width, label=name)
    ax.set(title="Independent validity rate — all attempts", xlabel="Number of agents", ylabel="Valid rate", xticks=counts, ylim=(0, 1.05))
    ax.legend()
    fig.savefig(asset_dir / f"{prefix}valid_rate_all_attempts.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    grouped = paired.groupby("num_agents", as_index=False).agg(
        paired_valid_instances=("paired_valid_instances", "sum"),
        median_soc_a_paired=("median_soc_a_paired", "median"),
        median_soc_b_paired=("median_soc_b_paired", "median"),
    )
    available = grouped[grouped["paired_valid_instances"] > 0]
    if not available.empty:
        ax.plot(available["num_agents"], available["median_soc_a_paired"], marker="o", label="prioritized")
        ax.plot(available["num_agents"], available["median_soc_b_paired"], marker="o", label="cbs")
        for row in available.itertuples():
            ax.annotate(f"paired n={row.paired_valid_instances}", (row.num_agents, row.median_soc_b_paired), xytext=(4, 6), textcoords="offset points", fontsize=8)
        ax.legend()
    ax.set(title="SOC on paired-valid instances only", xlabel="Number of agents", ylabel="Median sum of costs")
    fig.savefig(asset_dir / f"{prefix}paired_soc.png", dpi=160)
    plt.close(fig)


def run_instances(instances: list[BenchmarkInstance], *, output_dir: str | Path,
                  asset_dir: str | Path = "assets", asset_prefix: str = "",
                  cbs_timeout: float) -> pd.DataFrame:
    """Run solvers and write raw, aggregate, paired-detail, and paired-summary data."""
    records = [
        record_run(instance, algorithm, _safe_solve(algorithm, instance.problem, cbs_timeout), cbs_timeout)
        for instance in instances
        for algorithm in ("independent_astar", "prioritized", "cbs")
    ]
    results = pd.DataFrame(records, columns=RUN_COLUMNS)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    results.to_csv(destination / "results.csv", index=False)
    summary = summarize_runs(results)
    summary.to_csv(destination / "summary.csv", index=False)
    details = paired_valid_details(results)
    details.to_csv(destination / "paired_details.csv", index=False)
    paired = summarize_paired(results, details)
    paired.to_csv(destination / "paired_summary.csv", index=False)
    _plot_outputs(summary, paired, Path(asset_dir), asset_prefix)
    print(f"wrote {len(results)} attempts and {len(details)} paired-valid comparisons to {destination}")
    return results


def run_benchmark(*, quick: bool = False, larger: bool = False, counts: list[int] | None = None,
                  seeds: int | None = None, cbs_timeout: float | None = None) -> pd.DataFrame:
    """Run the synthetic smoke or larger reproducible benchmark."""
    del larger  # the flag documents intent; non-quick settings select the larger run
    counts = counts or ([5, 10, 15] if quick else [5, 10, 15, 20])
    seed_count = seeds if seeds is not None else (5 if quick else 10)
    timeout = cbs_timeout if cbs_timeout is not None else (0.6 if quick else 1.5)
    output = "benchmarks/smoke" if quick else "benchmarks/synthetic_larger"
    prefix = "smoke_" if quick else "synthetic_larger_"
    return run_instances(synthetic_instances(counts, seed_count), output_dir=output, asset_prefix=prefix, cbs_timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible MAPF benchmarks.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="5/10/15 agents × 5 seeds")
    mode.add_argument("--larger", action="store_true", help="5/10/15/20 agents × 10 seeds")
    parser.add_argument("--agents", nargs="+", type=int)
    parser.add_argument("--seeds", type=int)
    parser.add_argument("--cbs-timeout", type=float)
    args = parser.parse_args()
    run_benchmark(quick=args.quick, larger=args.larger, counts=args.agents, seeds=args.seeds, cbs_timeout=args.cbs_timeout)


if __name__ == "__main__":
    main()
