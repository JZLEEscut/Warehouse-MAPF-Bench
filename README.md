# Warehouse-MAPF-Bench

**Benchmarking Multi-Agent Path Finding Algorithms in Automated Warehouses**

A compact Python implementation and benchmark of A*, Prioritized Planning,
and Conflict-Based Search for collision-free multi-AGV routing on warehouse
grids.

![Warehouse MAPF demo](assets/demo.gif)

The animation is generated from validated Prioritized Planning paths for 8
AGVs on a deterministic 18 × 28 synthetic shelf-and-aisle map (seed 17).

## Why MAPF?

Independent shortest paths can put two AGVs in the same cell (a vertex
conflict) or make them exchange cells simultaneously (an edge-swap conflict).
MAPF represents both space and discrete time to avoid these collisions.

## Implemented algorithms

| Algorithm | Conflict aware | Notes | Role |
| --- | --- | --- | --- |
| Independent A* | No | Static shortest paths; conflicts are retained | Naive baseline |
| Prioritized Planning | Yes | Sequential reservations; incomplete and order-dependent | Fast heuristic |
| CBS | Yes | Standard constraint-tree branching with Space-Time A* | Small-instance exact-style baseline |

Space-Time A* searches `(row, column, time)`, supports `WAIT`, vertex
constraints, and directed edge constraints. A finite horizon bounds wait-state
expansion.

```text
Scenario
   ├── Independent A*
   ├── Prioritized Planning ── Space-Time A*
   └── CBS ─────────────────── Space-Time A*
             │
             ▼
   Independent validation
             │
             ▼
     Metrics / CSV / Plots / GIF
```

## Quick start

```bash
python -m pip install -r requirements.txt
pytest -q
python -m warehouse_mapf.demo
python -m warehouse_mapf.benchmark --quick
```

## Benchmark methodology

The checked-in quick benchmark uses 5, 10, and 15 agents with five seeds
(0–4), producing 45 measured runs. All three algorithms receive the same map,
starts, and goals for each `(agent count, seed)` pair. CBS has a 0.6 second
per-instance timeout; failed and timed-out rows remain in the result set.

`success` means the solver returned every path. `valid` additionally requires
an independent check of endpoints, obstacle avoidance, legal motion, vertex
conflicts, and edge swaps. Runtime is aggregated across all runs; path quality
uses successful, valid solutions only.

| Algorithm | Agents | Runs | Success | Valid | Median runtime (ms) | Median valid cost | Mean conflicts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CBS | 5 | 5 | 1.0 | 1.0 | 5.262 | 74.0 | 0.0 |
| CBS | 10 | 5 | 1.0 | 1.0 | 40.098 | 164.0 | 0.0 |
| CBS | 15 | 5 | 0.4 | 0.4 | 602.282 | 221.0 | 0.0 |
| Independent A* | 5 | 5 | 1.0 | 0.6 | 2.069 | 69.0 | 0.4 |
| Independent A* | 10 | 5 | 1.0 | 0.2 | 5.685 | 143.0 | 2.8 |
| Independent A* | 15 | 5 | 1.0 | 0.0 | 9.493 | — | 6.4 |
| Prioritized Planning | 5 | 5 | 1.0 | 1.0 | 11.479 | 74.0 | 0.0 |
| Prioritized Planning | 10 | 5 | 1.0 | 1.0 | 56.218 | 174.0 | 0.0 |
| Prioritized Planning | 15 | 5 | 1.0 | 1.0 | 134.573 | 255.0 | 0.0 |

The source data are in
[`benchmarks/results.csv`](benchmarks/results.csv) and
[`benchmarks/summary.csv`](benchmarks/summary.csv). Three 15-agent CBS runs
timed out and are retained honestly in the CSV and aggregate rates.

![Runtime versus agents](assets/runtime_vs_agents.png)

![Path cost versus agents](assets/cost_vs_agents.png)

On this quick benchmark, Prioritized Planning returned valid solutions for all
15 paired instances. CBS found lower median cost than Prioritized Planning at
10 agents (164 versus 174), but solved only 2 of 5 instances at 15 agents
within the configured limit. Independent A* is fastest but increasingly
conflict-prone, so it is excluded from the feasible path-cost chart.

## Correctness

The test suite covers shortest paths, obstacles, unreachable goals, vertex and
edge conflicts, goal holding, constrained waits, future goal constraints,
Prioritized Planning, CBS, independent validation, and deterministic scenario
generation. Solver results are revalidated before benchmark rows can be marked
valid.

## Repository layout

```text
src/warehouse_mapf/   algorithms, validation, scenarios, CLI, visualization
tests/                correctness and integration tests
benchmarks/           measured run-level and aggregate CSVs
assets/               generated GIF and benchmark plots
docs/                 algorithm and experiment notes
```

## Limitations

- Discrete grids do not model acceleration, turning radius, or continuous collision avoidance.
- The project solves routing, not task assignment, scheduling, charging, or warehouse control.
- Prioritized Planning is incomplete and depends on agent order.
- CBS runtime scales poorly on difficult instances; the included timeout is a practical guardrail.
- Scenarios are deterministic synthetic warehouse layouts, not operational telemetry.

## References

- Stern et al., *Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks*, SoCS 2019. [Moving AI MAPF benchmarks](https://www.movingai.com/benchmarks/mapf.html)
- Sharon et al., *Conflict-Based Search for Optimal Multi-Agent Pathfinding*, Artificial Intelligence 219, 2015.

## Resume summary

Implemented A*, Space-Time A*, Prioritized Planning, and Conflict-Based Search
for warehouse MAPF; built an independent collision validator and reproducible
paired benchmark across three agent scales and five seeds; evaluated runtime,
success, validity, makespan, sum-of-costs, and conflicts while producing an
animated multi-AGV visualization.
