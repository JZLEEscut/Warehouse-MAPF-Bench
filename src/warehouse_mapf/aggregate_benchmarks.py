"""Combine already measured benchmark components into one auditable study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .benchmark import RUN_COLUMNS
from .reporting import paired_valid_details, summarize_paired, summarize_runs


def combine_result_files(inputs: list[str | Path], output_dir: str | Path) -> pd.DataFrame:
    """Combine run-level files and regenerate every derived table."""
    paths = [Path(path) for path in inputs]
    frames = [pd.read_csv(path) for path in paths]
    for path, frame in zip(paths, frames):
        missing = set(RUN_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"{path}: missing run columns {sorted(missing)}")
    combined = pd.concat(frames, ignore_index=True)[RUN_COLUMNS]
    if combined.duplicated(["algorithm", "instance_id"]).any():
        raise ValueError("duplicate algorithm/instance pairs in combined results")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    combined.to_csv(destination / "results.csv", index=False)
    summarize_runs(combined).to_csv(destination / "summary.csv", index=False)
    details = paired_valid_details(combined)
    details.to_csv(destination / "paired_details.csv", index=False)
    summarize_paired(combined, details).to_csv(destination / "paired_summary.csv", index=False)
    manifest = {"inputs": [path.as_posix() for path in paths], "attempted_runs": len(combined)}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine raw MAPF result CSVs and regenerate summaries.")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    combined = combine_result_files(args.inputs, args.output_dir)
    print(f"combined {len(combined)} attempted runs into {args.output_dir}")


if __name__ == "__main__":
    main()
