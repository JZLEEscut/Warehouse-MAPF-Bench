# Moving AI warehouse data provenance

This directory contains a small, reproducible official-data subset used by the
v0.2 benchmark.

- Source: Moving AI MAPF Benchmarks, https://www.movingai.com/benchmarks/mapf/
- Map archive: https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map.zip
- Scenario archive: https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map-scen-even.zip
- Selected source scenario: `warehouse-10-20-10-2-1-even-1.scen`
- Retrieved: 2026-09-20
- License: Open Data Commons Attribution License, as stated on the official
  Moving AI MAPF benchmark page.

The map and one complete official scenario file are committed. Exact row IDs
used for every recorded instance are stored in
`benchmarks/movingai/selection_manifest.json` and repeated in the run-level
CSV. The selection procedure is a deterministic seeded permutation followed
by filtering for unique starts and unique goals.

Terrain policy: `.`, `G`, and `S` are traversable; `@`, `T`, `O`, and `W` are
blocked. Any other terrain symbol is rejected rather than guessed. Moving AI
`(x, y)` coordinates are converted once at the parser boundary to this
project's `(row, column)` convention.

Reproduce the recorded run from the repository root:

```bash
python -m warehouse_mapf.standard_benchmark \
  --map data/movingai/warehouse-10-20-10-2-1.map \
  --scen data/movingai/warehouse-10-20-10-2-1-even-1.scen \
  --agents 5 10 --selection-seeds 0 1 2 --cbs-timeout 0.6 \
  --retrieval-date 2026-09-20 \
  --map-url https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map.zip \
  --scen-url https://movingai.com/benchmarks/mapf/warehouse-10-20-10-2-1.map-scen-even.zip
```
