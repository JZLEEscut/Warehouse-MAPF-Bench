"""Guard the unit of pairing and the reproducibility contract."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from warehouse_mapf import improvement_study as study
from warehouse_mapf.benchmark import BenchmarkInstance
from warehouse_mapf.cases import make_case


def test_repeated_runs_are_paired_without_inflating_unique_instances(monkeypatch):
    monkeypatch.setattr(study, "synthetic_instances", lambda counts, seeds: [
        BenchmarkInstance(make_case("crossing"), "synthetic", "tiny", "tiny", "tiny:n2", 0)])
    monkeypatch.setattr(study, "plot_study", lambda *args: None)
    with TemporaryDirectory(dir=Path(__file__).parent / ".tmp") as directory:
        destination = Path(directory)
        frame = study.run_study(destination, repetitions=2, seeds=1, timeout=1)
        assert len(frame) == 40
        assert not frame.duplicated(["algorithm", "instance_id"]).any()
        import pandas as pd
        paired = pd.read_csv(destination / "paired_summary.csv")
        group = paired[(paired.source == "synthetic") & (paired.algorithm_a == "cbs_manhattan")].iloc[0]
        assert group.paired_valid_runs == 2 and group.paired_unique_instances == 1
        manifest = json.loads((destination / "environment.json").read_text(encoding="utf-8"))
        assert "cbs.py" in manifest["source_sha256"]
        assert manifest["parameters"]["repetitions"] == 2
        replays = json.loads((destination / "case_replays.json").read_text(encoding="utf-8"))
        assert replays["goal_hold:pp_longest_static"]["valid"]
