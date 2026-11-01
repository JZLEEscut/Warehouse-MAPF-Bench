# Algorithms

All coordinates are `(row, column)`. Agents move synchronously with four
cardinal moves or `WAIT`.

- A* finds static shortest paths with Manhattan distance.
- Space-Time A* searches `(position, time)` and enforces vertex and directed
  edge constraints with a finite time horizon.
- Prioritized Planning reserves earlier paths and their held goal cells.
- CBS branches on the earliest conflict and replans only one affected agent.

CBS passes one absolute deadline through its high-level and low-level searches.
`timeout` is distinct from search exhaustion or a finite-horizon cutoff. CBS is
sum-of-costs optimal only when the standard constraint-tree search completes
without hitting configured time, expansion, or horizon limits.

The independent validator checks endpoints, legal motion, obstacles, vertex
collisions, and edge swaps without relying on solver internals.

## v0.3 optional search improvements

`solve_cbs(..., heuristic="static")` and `solve_prioritized(..., heuristic="static")`
use exact static distances from reverse BFS as admissible, consistent lower bounds.
Each solver owns a grid-bound goal cache; repeated CBS low-level replans reuse it,
but separate solves do not. Manhattan remains the default. Preprocessing is counted
in runtime and shares the search deadline. Metadata separates `low_level_calls`,
`low_level_expanded`, `precompute_ms`, `precompute_cells`, and `distance_cache_hits`
from CBS high-level `expanded_nodes`.

`solve_prioritized(..., order="longest_first", timeout_s=...)` stably orders agents
by descending static shortest distance. This changes priority only; it does not
provide completeness or global optimality. Its BFS ordering cost is included.

For CBS root failure, static reachability is checked within the remaining deadline:
reachable-but-cutoff is `no_solution_within_limits`, disconnected is `no_solution`,
and interruption of that check is `timeout`. Goal acceptance also considers future
goal-to-goal WAIT edge constraints, because returned goals are held permanently.
