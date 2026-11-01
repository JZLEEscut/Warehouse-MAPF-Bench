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

## v0.3 Improvement study

Run from the repository root:

```bash
python -m warehouse_mapf.improvement_study
```

The recorded run on 2026-11-01 uses committed solver code `ebdfbe4`, Python
3.11.5 on Windows, and a clean tracked worktree at the start. See
[`environment.json`](../benchmarks/v0_3_improvements/environment.json) for CPU,
package versions, full parameters, source hashes and timing policy. Source hashes
use UTF-8 text with normalized newlines, so Windows/Linux line endings do not
change the digest. These results are separate from the historical v0.2 study.

### Configuration and units

- Synthetic map: 18 × 28, 5/10/15 agents, seeds 0–4: **15 unique instances**.
- Diagnostic cases: corridor, crossing and goal_hold: **3 unique instances**.
- Five variants: CBS Manhattan/static BFS, Prioritized Manhattan/static BFS,
  and Prioritized longest-first with static BFS.
- Each variant runs three times per instance: **270 solver attempts total**.
- A fresh per-solve cache for every attempt; preprocessing and ordering count
  toward the same 0.6-second wall-time budget. Horizon is grid area + 10.
- Variant execution order is shuffled with a fixed seed of 2026. This reduces
  systematic order effects but does not eliminate machine load or timing noise.
- The final recorded run did not run the project test suite concurrently.
- Low-level calls and expanded states are distinct from CBS constraint-tree
  expansions. Precompute cells, milliseconds and cache hits are also recorded.

原始结果保存所有尝试，包括失败和超时。配对键包含原始实例和 repetition，
避免不同次运行混配；配对表同时报告 paired_valid_runs 与
paired_unique_instances。三次计时重复不能当成三个独立规划问题。

The raw table includes failures and timeouts. Pairing uses instance + repetition;
repeated timings and unique planning instances are reported separately. No
statistical independence or significance claim is made from repeated timings.

### Recorded paired results: synthetic instances

| Comparison | Paired runs / unique instances | Median time A → B (ms) | Median low-level expansions A → B | Median per-run SOC(A) − SOC(B) |
| --- | ---: | ---: | ---: | ---: |
| CBS Manhattan → static | 36 / 12 | 32.0675 → 50.135 | 1414.5 → 1312.5 | 0 |
| Prioritized Manhattan → static | 45 / 15 | 100.715 → 101.517 | 678 → 601 | 0 |
| Prioritized static → longest-first static | 45 / 15 | 101.517 → 121.957 | 601 → 968 | −1 |

Each CBS variant validated on 36/45 synthetic attempts (12/15 unique instances);
the other nine attempts per CBS variant timed out. All three Prioritized
variants validated on 45/45 attempts (15/15 unique instances).

The static heuristic reduced the recorded paired median expansion counts,
but did **not** improve the paired median wall time in this sample. Repeated
goal preprocessing has a cost, and the existing reservation and conflict
handling still does work outside the heuristic. The experiment measures total
time; it does not establish a detailed profiler attribution. Manhattan remains
the default. No speedup percentage is claimed.

Longest-first also did not improve the aggregate synthetic SOC: the median
per-run difference of −1 means its SOC was one higher on that comparison.
It is a diagnostic strategy, not a universally better replacement.

静态启发式在这组实验中减少扩展但没有缩短中位总耗时；排序策略也不是普遍更优。
该结果说明需要把预处理成本、成功率和解质量一起评估，不能只凭一个内部计数宣称优化成功。

### Diagnostic cases

| Case | CBS (both heuristics) | Prioritized input order (both heuristics) | Prioritized longest-first static |
| --- | --- | --- | --- |
| crossing | valid, SOC 5 | valid | valid |
| corridor | valid | no_solution_within_limits | no_solution_within_limits |
| goal_hold | valid | no_solution_within_limits | valid |

The three repetitions show the same case outcomes. goal_hold demonstrates a
specific ordering benefit: moving the long-route agent first prevents another
agent from parking permanently at its intersection. corridor demonstrates the
remaining limitation: a fixed earlier straight path cannot yield to a later
agent, while CBS can revise either path.

Validated and partial paths for all case variants are recorded in
[`case_replays.json`](../benchmarks/v0_3_improvements/case_replays.json).
The live demo additionally exposes Independent A* to inspect baseline conflicts.

### Artifacts and verification

- `results.csv`: all 270 attempts, outcomes, timing and instrumentation.
- `summary.csv`: all-attempt counts/rates by source, map, scale and variant.
- `paired_details.csv`: repeated-run pairs including timing, expansions and SOC.
- `paired_summary.csv`: paired medians, attempt counts and unique-instance counts.
- `case_replays.json`: first-repetition solver paths, independent validation and conflicts.
- `environment.json`: code revision, normalized source hashes and environment.
- `assets/improvement_ablation.png`: synthetic all-attempt medians, including
  timeout attempts, with validity denominators. Its values need not equal the
  paired-valid medians in the table above.

Verification includes 34 passing tests, real loopback HTTP checks, JavaScript
syntax checking and checking the built wheel contains the HTML resource.
Native browser visual inspection was stopped by Computer Use because it could
not establish the browser URL; no completed visual browser check is claimed.
