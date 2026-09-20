import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from warehouse_mapf.benchmark import RUN_COLUMNS
from warehouse_mapf.aggregate_benchmarks import combine_result_files


def test_combiner_regenerates_tables():
    base = {name: None for name in RUN_COLUMNS}
    rows = []
    for algorithm, soc in (("prioritized", 10), ("cbs", 9)):
        row = dict(base)
        row.update({
            "source": "fixture", "map_id": "tiny", "scenario_id": "one", "selection_row_ids": "-",
            "instance_id": "tiny:n2:one", "algorithm": algorithm, "seed": 0, "num_agents": 2,
            "outcome": "solved", "success": True, "valid": True, "timed_out": False,
            "runtime_ms": 1.0, "sum_of_costs": soc, "makespan": 5, "conflicts": 0,
            "validation_error": "", "failure_reason": "", "expanded_nodes": 1, "limit_seconds": None,
        })
        rows.append(row)
    parent = Path(__file__).parent / ".tmp"
    with TemporaryDirectory(dir=parent) as directory:
        source = Path(directory) / "source.csv"
        output = Path(directory) / "combined"
        pd.DataFrame(rows, columns=RUN_COLUMNS).to_csv(source, index=False)
        combined = combine_result_files([source], output)
        assert len(combined) == 2
        assert (output / "paired_summary.csv").exists()
        paired = pd.read_csv(output / "paired_summary.csv")
        assert paired.loc[0, "paired_valid_instances"] == 1
