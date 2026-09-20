import pandas as pd

from warehouse_mapf.reporting import paired_valid_details, summarize_paired, summarize_runs


def _row(instance, algorithm, *, success, valid, outcome, runtime, soc=None, makespan=None):
    return {
        "source": "fixture", "map_id": "tiny", "num_agents": 4,
        "instance_id": instance, "scenario_id": instance, "selection_row_ids": "",
        "algorithm": algorithm, "success": success, "valid": valid,
        "timed_out": outcome == "timeout", "outcome": outcome,
        "runtime_ms": runtime, "sum_of_costs": soc, "makespan": makespan,
    }


def test_outcome_denominators_and_paired_intersection():
    frame = pd.DataFrame([
        _row("easy", "prioritized", success=True, valid=True, outcome="solved", runtime=2, soc=10, makespan=6),
        _row("hard", "prioritized", success=True, valid=True, outcome="solved", runtime=3, soc=20, makespan=11),
        _row("easy", "cbs", success=True, valid=True, outcome="solved", runtime=5, soc=9, makespan=5),
        _row("hard", "cbs", success=False, valid=False, outcome="timeout", runtime=100, soc=None, makespan=None),
        _row("invalid", "cbs", success=True, valid=False, outcome="solved", runtime=7, soc=8, makespan=5),
        _row("invalid", "prioritized", success=False, valid=False, outcome="no_solution_within_limits", runtime=4),
    ])
    summary = summarize_runs(frame)
    cbs = summary[summary.algorithm == "cbs"].iloc[0]
    assert cbs.attempted_instances == 3
    assert cbs.solved_instances == 2
    assert cbs.valid_instances == 1
    assert cbs.timed_out_instances == 1
    assert cbs.success_rate != cbs.valid_rate
    assert cbs.median_runtime_ms_all_attempts == 7

    details = paired_valid_details(frame)
    assert details.instance_id.tolist() == ["easy"]
    assert details.soc_delta_a_minus_b.tolist() == [1]
    paired = summarize_paired(frame, details).iloc[0]
    assert paired.attempted_instances == 3
    assert paired.paired_valid_instances == 1
    assert paired.median_soc_a_paired == 10
    assert paired.median_soc_b_paired == 9


def test_missing_paired_intersection_is_na_not_zero():
    frame = pd.DataFrame([
        _row("a", "prioritized", success=True, valid=True, outcome="solved", runtime=2, soc=10, makespan=5),
        _row("a", "cbs", success=False, valid=False, outcome="timeout", runtime=100),
    ])
    details = paired_valid_details(frame)
    assert details.empty
    paired = summarize_paired(frame, details).iloc[0]
    assert paired.paired_valid_instances == 0
    assert pd.isna(paired.median_soc_a_paired)
    assert pd.isna(paired.median_soc_b_paired)
