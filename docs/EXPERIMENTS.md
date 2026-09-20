# Experiments and reporting semantics

## Run-level fields

Every attempted solver run is retained in `results.csv`.

- `outcome` is one of `solved`, `timeout`, `no_solution`,
  `no_solution_within_limits`, or `error`.
- `success=True` means a complete path set was returned before the configured
  limit. It does not imply correctness.
- `valid=True` additionally means the independent validator accepted every
  endpoint, cell, move, vertex interaction, edge interaction, and held goal.
- `timed_out=True` exactly when `outcome=timeout`.
- `runtime_ms` is measured for every attempt, including failures and timeouts.
- `instance_id` identifies the immutable map, scale, seed/selection, and (for
  Moving AI) exact scenario row IDs.

Because the planners use finite time horizons, a constrained search that ends
without a path is conservatively labeled `no_solution_within_limits`. Only a
root static-connectivity failure is labeled `no_solution`.

## Paired quality

Path quality is never compared across different solved subsets. For each map
and agent count, `paired_details.csv` contains only instance IDs for which both
Prioritized Planning and CBS returned independently valid paths. The delta is:

```text
SOC delta = SOC(Prioritized) - SOC(CBS)
```

A positive value favors CBS. `paired_summary.csv` reports the paired-valid
sample count beside all SOC and makespan medians. When the intersection is
empty, quality values are blank (`N/A`), never zero.

## Recorded experiments

### Smoke

```bash
python -m warehouse_mapf.benchmark --quick
```

Synthetic 18 × 28 warehouse; 5/10/15 agents; seeds 0–4; CBS timeout 0.6 s.

### Larger synthetic

```bash
python -m warehouse_mapf.benchmark --larger
```

Synthetic 18 × 28 warehouse; 5/10/15/20 agents; seeds 0–9; CBS timeout 1.5 s.
The configuration is stored in `benchmarks/synthetic_larger/config.json`.

### Official Moving AI warehouse subset

```bash
python -m warehouse_mapf.standard_benchmark \
  --map data/movingai/warehouse-10-20-10-2-1.map \
  --scen data/movingai/warehouse-10-20-10-2-1-even-1.scen \
  --agents 5 10 --selection-seeds 0 1 2 --cbs-timeout 0.6 \
  --retrieval-date 2026-09-20 \
  --map-url https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map.zip \
  --scen-url https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map-scen-even.zip
```

The source is the official Moving AI MAPF benchmark collection. The committed
manifest records source URLs, retrieval date, license statement, selection
method, and exact row IDs. The official 161 × 63 map and one complete scenario
file are stored under `data/movingai/`.

### Combined v0.2 study

```bash
python -m warehouse_mapf.aggregate_benchmarks \
  benchmarks/synthetic_larger/results.csv benchmarks/movingai/results.csv \
  --output-dir benchmarks/v0_2_study
```

This creates one 138-attempt auditable run table while preserving separate
source/map groupings in every summary and paired comparison.

## Interpretation limits

Runtime includes all attempts, including timeouts. Independent A* remains an
infeasible baseline when it conflicts. CBS quality is discussed only on the
paired-valid subset and no optimality claim is made for timed-out or cutoff
runs. These small synthetic and benchmark subsets are reproducibility examples,
not industrial warehouse performance evidence.
