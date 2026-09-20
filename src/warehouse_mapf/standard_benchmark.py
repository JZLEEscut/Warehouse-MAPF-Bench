"""Run deterministic subsets of official Moving AI MAPF scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import BenchmarkInstance, run_instances
from .movingai import load_movingai_map, load_movingai_scen, problem_from_scenario, select_scenario_rows

OFFICIAL_PAGE = "https://www.movingai.com/benchmarks/mapf/"


def build_movingai_instances(
    map_path: str | Path,
    scen_path: str | Path,
    *,
    counts: list[int],
    selection_seeds: list[int],
) -> tuple[list[BenchmarkInstance], list[dict[str, object]]]:
    """Build reproducible instances and their auditable selected-row manifest."""
    map_path, scen_path = Path(map_path), Path(scen_path)
    grid = load_movingai_map(map_path)
    scenario_rows = load_movingai_scen(scen_path)
    instances: list[BenchmarkInstance] = []
    selections: list[dict[str, object]] = []
    for count in counts:
        for seed in selection_seeds:
            selected = select_scenario_rows(
                scenario_rows, grid, count=count, strategy="random", seed=seed,
                expected_map_name=map_path.name,
            )
            row_ids = [row.row_id for row in selected]
            row_text = ",".join(map(str, row_ids))
            instance_id = f"movingai:{map_path.stem}:n{count}:selection{seed}:rows-{row_text}"
            instances.append(BenchmarkInstance(
                problem_from_scenario(grid, selected, expected_map_name=map_path.name),
                "movingai", map_path.name, f"{scen_path.name}:selection-{seed}",
                instance_id, seed, row_text,
            ))
            selections.append({"instance_id": instance_id, "num_agents": count, "selection_seed": seed, "row_ids": row_ids})
    return instances, selections


def run_standard_benchmark(
    map_path: str | Path,
    scen_path: str | Path,
    *,
    counts: list[int],
    selection_seeds: list[int],
    cbs_timeout: float,
    output_dir: str | Path = "benchmarks/movingai",
    retrieval_date: str = "unknown",
    map_url: str = "",
    scen_url: str = "",
) -> None:
    """Run an official-data subset and write its provenance/selection manifest."""
    instances, selections = build_movingai_instances(map_path, scen_path, counts=counts, selection_seeds=selection_seeds)
    destination = Path(output_dir)
    run_instances(instances, output_dir=destination, asset_prefix="movingai_", cbs_timeout=cbs_timeout)
    manifest = {
        "source": "Moving AI MAPF Benchmarks",
        "official_page": OFFICIAL_PAGE,
        "license": "Open Data Commons Attribution License (as stated by Moving AI)",
        "retrieval_date": retrieval_date,
        "map_file": Path(map_path).name,
        "scenario_file": Path(scen_path).name,
        "map_url": map_url,
        "scenario_url": scen_url,
        "selection_strategy": "seeded random permutation followed by unique start/goal filtering",
        "counts": counts,
        "selection_seeds": selection_seeds,
        "cbs_timeout_seconds": cbs_timeout,
        "selections": selections,
    }
    (destination / "selection_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark an official Moving AI map/scenario subset.")
    parser.add_argument("--map", required=True)
    parser.add_argument("--scen", required=True)
    parser.add_argument("--agents", nargs="+", type=int, default=[5, 10])
    parser.add_argument("--selection-seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--cbs-timeout", type=float, default=0.6)
    parser.add_argument("--output-dir", default="benchmarks/movingai")
    parser.add_argument("--retrieval-date", default="unknown")
    parser.add_argument("--map-url", default="")
    parser.add_argument("--scen-url", default="")
    args = parser.parse_args()
    run_standard_benchmark(
        args.map, args.scen, counts=args.agents, selection_seeds=args.selection_seeds,
        cbs_timeout=args.cbs_timeout, output_dir=args.output_dir, retrieval_date=args.retrieval_date,
        map_url=args.map_url, scen_url=args.scen_url,
    )


if __name__ == "__main__":
    main()
