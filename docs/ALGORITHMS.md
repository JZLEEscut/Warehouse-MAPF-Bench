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
