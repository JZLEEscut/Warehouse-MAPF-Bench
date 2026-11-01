"""Cold-cache, shuffled-order ablations without overwriting historical v0.2 data."""

import argparse
import json
from pathlib import Path
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .benchmark import BenchmarkInstance, record_run, synthetic_instances
from .cases import CASE_DESCRIPTIONS, make_case
from .cbs import solve_cbs
from .prioritized import solve_prioritized
from .provenance import write_environment
from .replay import replay_payload
from .reporting import paired_valid_details, summarize_runs

VARIANTS = {
    "cbs_manhattan": ("cbs", "manhattan", "input"),
    "cbs_static": ("cbs", "static", "input"),
    "pp_manhattan": ("pp", "manhattan", "input"),
    "pp_static": ("pp", "static", "input"),
    "pp_longest_static": ("pp", "static", "longest_first"),
}


def solve_variant(problem, variant: str, timeout: float, max_time: int | None = None):
    solver, heuristic, order = VARIANTS[variant]
    if solver == "cbs":
        return solve_cbs(problem, heuristic=heuristic, timeout_s=timeout, max_time=max_time)
    return solve_prioritized(problem, heuristic=heuristic, order=order, timeout_s=timeout, max_time=max_time)


def run_study(output_dir: Path, *, repetitions: int = 3, seeds: int = 5,
              timeout: float = 0.6, asset_dir: Path = Path("assets")) -> pd.DataFrame:
    if repetitions < 1 or seeds < 1 or timeout <= 0:
        raise ValueError("repetitions, seeds and timeout must be positive")
    instances = synthetic_instances([5, 10, 15], seeds)
    for name in CASE_DESCRIPTIONS:
        problem = make_case(name)
        instances.append(BenchmarkInstance(problem, "case", name, name, f"case:{name}", 0))
    output_dir.mkdir(parents=True, exist_ok=True)
    write_environment(output_dir, {
        "repetitions": repetitions, "seeds": seeds, "timeout_seconds": timeout,
        "counts": [5, 10, 15], "cases": list(CASE_DESCRIPTIONS),
        "variants": VARIANTS, "order_seed": 2026,
        "cache_policy": "new per-solve cache; preprocessing included in runtime; no cross-run reuse",
        "horizon_policy": "grid area + 10, identical across compared variants",
        "instance_ids": [i.instance_id for i in instances],
    })
    records = []
    replay_cases = {}
    rng = random.Random(2026)
    for instance in instances:
        for repetition in range(repetitions):
            order = list(VARIANTS)
            rng.shuffle(order)
            for sequence, variant in enumerate(order):
                solution = solve_variant(instance.problem, variant, timeout)
                record = record_run(instance, variant, solution, timeout)
                record.update(solution.metadata)
                record.update({"base_instance_id": instance.instance_id, "repetition": repetition,
                               "execution_order": sequence, "limit_seconds": timeout,
                               "instance_id": f"{instance.instance_id}:rep{repetition}"})
                records.append(record)
                if instance.source == "case" and repetition == 0:
                    replay_cases[f"{instance.map_id}:{variant}"] = replay_payload(instance.problem, solution)
    frame = pd.DataFrame(records)
    frame.to_csv(output_dir / "results.csv", index=False)
    summarize_runs(frame).to_csv(output_dir / "summary.csv", index=False)
    summaries, all_details = [], []
    for a, b in (("cbs_manhattan", "cbs_static"), ("pp_manhattan", "pp_static"),
                 ("pp_static", "pp_longest_static")):
        details = paired_valid_details(frame, a, b)
        if not details.empty:
            left = frame[frame.algorithm == a].set_index("instance_id")
            right = frame[frame.algorithm == b].set_index("instance_id")
            details["runtime_a_ms"] = details.instance_id.map(left.runtime_ms)
            details["runtime_b_ms"] = details.instance_id.map(right.runtime_ms)
            details["low_level_expanded_a"] = details.instance_id.map(left.low_level_expanded)
            details["low_level_expanded_b"] = details.instance_id.map(right.low_level_expanded)
            details["base_instance_id"] = details.instance_id.map(left.base_instance_id)
            all_details.append(details)
        for source in ("synthetic", "case"):
            group = details[details.source == source]
            attempted = frame[(frame.source == source) & (frame.algorithm == a)]
            valid_a = attempted.valid.sum()
            valid_b = frame[(frame.source == source) & (frame.algorithm == b)].valid.sum()
            summaries.append({
                "source": source, "algorithm_a": a, "algorithm_b": b,
                "attempts_per_variant": len(attempted), "valid_a": valid_a, "valid_b": valid_b,
                "paired_valid_runs": len(group),
                "paired_unique_instances": group.base_instance_id.nunique() if len(group) else 0,
                "median_paired_runtime_a_ms": group.runtime_a_ms.median() if len(group) else None,
                "median_paired_runtime_b_ms": group.runtime_b_ms.median() if len(group) else None,
                "median_paired_expanded_a": group.low_level_expanded_a.median() if len(group) else None,
                "median_paired_expanded_b": group.low_level_expanded_b.median() if len(group) else None,
                "median_soc_delta_a_minus_b": group.soc_delta_a_minus_b.median() if len(group) else None,
            })
    combined = pd.concat(all_details, ignore_index=True) if all_details else paired_valid_details(frame)
    combined.to_csv(output_dir / "paired_details.csv", index=False)
    pd.DataFrame(summaries).to_csv(output_dir / "paired_summary.csv", index=False)
    (output_dir / "case_replays.json").write_text(json.dumps(replay_cases, ensure_ascii=False), encoding="utf-8")
    plot_study(frame, asset_dir)
    print(f"Saved {len(frame)} real attempts to {output_dir}")
    return frame


def plot_study(frame: pd.DataFrame, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    synthetic = frame[frame.source == "synthetic"]
    names = list(VARIANTS)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    labels = [n.replace("_", "\n", 1) for n in names]
    for ax, column, title, unit in (
        (axes[0], "runtime_ms", "All-attempt median wall time", "ms (log scale; preprocessing included)"),
        (axes[1], "low_level_expanded", "All-attempt median low-level expansions", "states (log scale)"),
    ):
        values = [synthetic[synthetic.algorithm == n][column].median() for n in names]
        ax.scatter(range(len(names)), values, s=80,
                   c=["#64748b", "#147d92", "#64748b", "#147d92", "#c27a24"])
        ax.set_xticks(range(len(names)), labels)
        ax.set_xlim(-0.6, len(names) - 0.4)
        ax.set(title=title, ylabel=unit, yscale="log")
        ax.grid(axis="y", alpha=0.2)
        for i, (n, value) in enumerate(zip(names, values)):
            group = synthetic[synthetic.algorithm == n]
            ax.annotate(f"{value:.1f}\nvalid {int(group.valid.sum())}/{len(group)}", (i, value),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)
        ax.margins(y=0.35)
    fig.suptitle("v0.3 ablation · repeated runs are not independent instances")
    fig.savefig(destination / "improvement_ablation.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/v0_3_improvements"))
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=0.6)
    args = parser.parse_args()
    run_study(args.output_dir, repetitions=args.repetitions, seeds=args.seeds, timeout=args.timeout)


if __name__ == "__main__":
    main()
