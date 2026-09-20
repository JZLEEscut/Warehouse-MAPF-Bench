"""Auditable aggregate and paired-valid benchmark reporting."""

from __future__ import annotations

import pandas as pd

GROUP_KEYS = ["source", "map_id", "num_agents"]


def summarize_runs(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize outcomes over every attempted run without dropping failures."""
    records: list[dict[str, object]] = []
    for keys, group in frame.groupby([*GROUP_KEYS, "algorithm"], sort=True, dropna=False):
        source, map_id, num_agents, algorithm = keys
        outcomes = group["outcome"].value_counts()
        records.append({
            "source": source, "map_id": map_id, "num_agents": num_agents, "algorithm": algorithm,
            "attempted_instances": len(group), "solved_instances": int(group["success"].sum()),
            "valid_instances": int(group["valid"].sum()), "timed_out_instances": int(group["timed_out"].sum()),
            "success_rate": float(group["success"].mean()), "valid_rate": float(group["valid"].mean()),
            "timeout_rate": float(group["timed_out"].mean()),
            "median_runtime_ms_all_attempts": float(group["runtime_ms"].median()),
            "mean_runtime_ms_all_attempts": float(group["runtime_ms"].mean()),
            "outcome_solved": int(outcomes.get("solved", 0)), "outcome_timeout": int(outcomes.get("timeout", 0)),
            "outcome_no_solution": int(outcomes.get("no_solution", 0)),
            "outcome_no_solution_within_limits": int(outcomes.get("no_solution_within_limits", 0)),
            "outcome_error": int(outcomes.get("error", 0)),
        })
    return pd.DataFrame(records)


def paired_valid_details(frame: pd.DataFrame, algorithm_a: str = "prioritized", algorithm_b: str = "cbs") -> pd.DataFrame:
    """Return one row per instance valid for both named algorithms."""
    columns = ["source", "map_id", "num_agents", "instance_id", "scenario_id", "selection_row_ids",
               "algorithm_a", "algorithm_b", "soc_a", "soc_b", "soc_delta_a_minus_b",
               "makespan_a", "makespan_b", "makespan_delta_a_minus_b"]
    left = frame[(frame["algorithm"] == algorithm_a) & frame["valid"]].copy()
    right = frame[(frame["algorithm"] == algorithm_b) & frame["valid"]].copy()
    if left.empty or right.empty:
        return pd.DataFrame(columns=columns)
    identifiers = ["source", "map_id", "num_agents", "instance_id", "scenario_id", "selection_row_ids"]
    merged = left.merge(right, on=identifiers, how="inner", suffixes=("_a", "_b"), validate="one_to_one")
    detail = pd.DataFrame({
        **{name: merged[name] for name in identifiers}, "algorithm_a": algorithm_a, "algorithm_b": algorithm_b,
        "soc_a": merged["sum_of_costs_a"], "soc_b": merged["sum_of_costs_b"],
        "soc_delta_a_minus_b": merged["sum_of_costs_a"] - merged["sum_of_costs_b"],
        "makespan_a": merged["makespan_a"], "makespan_b": merged["makespan_b"],
        "makespan_delta_a_minus_b": merged["makespan_a"] - merged["makespan_b"],
    })
    return detail[columns].sort_values(["source", "map_id", "num_agents", "instance_id"]).reset_index(drop=True)


def summarize_paired(frame: pd.DataFrame, details: pd.DataFrame | None = None,
                     algorithm_a: str = "prioritized", algorithm_b: str = "cbs") -> pd.DataFrame:
    """Summarize quality only on the exact intersection of valid instances."""
    details = paired_valid_details(frame, algorithm_a, algorithm_b) if details is None else details
    records: list[dict[str, object]] = []
    groups = frame[frame["algorithm"].isin([algorithm_a, algorithm_b])].groupby(GROUP_KEYS, sort=True, dropna=False)
    for keys, group in groups:
        source, map_id, num_agents = keys
        attempted = set(group.loc[group["algorithm"] == algorithm_a, "instance_id"]) & set(group.loc[group["algorithm"] == algorithm_b, "instance_id"])
        a_valid = set(group.loc[(group["algorithm"] == algorithm_a) & group["valid"], "instance_id"])
        b_valid = set(group.loc[(group["algorithm"] == algorithm_b) & group["valid"], "instance_id"])
        paired = details[(details["source"] == source) & (details["map_id"] == map_id) & (details["num_agents"] == num_agents)]
        records.append({
            "source": source, "map_id": map_id, "num_agents": num_agents,
            "algorithm_a": algorithm_a, "algorithm_b": algorithm_b,
            "attempted_instances": len(attempted), "valid_instances_a": len(a_valid), "valid_instances_b": len(b_valid),
            "paired_valid_instances": len(paired),
            "median_soc_a_paired": float(paired["soc_a"].median()) if not paired.empty else None,
            "median_soc_b_paired": float(paired["soc_b"].median()) if not paired.empty else None,
            "median_soc_delta_a_minus_b": float(paired["soc_delta_a_minus_b"].median()) if not paired.empty else None,
            "median_makespan_a_paired": float(paired["makespan_a"].median()) if not paired.empty else None,
            "median_makespan_b_paired": float(paired["makespan_b"].median()) if not paired.empty else None,
            "median_makespan_delta_a_minus_b": float(paired["makespan_delta_a_minus_b"].median()) if not paired.empty else None,
        })
    return pd.DataFrame(records)
