# Algorithms

All coordinates are `(row, column)`. Agents move synchronously with four
cardinal moves or `WAIT`.

- A* finds static shortest paths with Manhattan distance.
- Space-Time A* searches `(position, time)` and enforces vertex and directed
  edge constraints with a finite time horizon.
- Prioritized Planning reserves earlier paths and their held goal cells.
- CBS branches on the earliest conflict and replans only one affected agent.

The independent validator checks endpoints, legal motion, obstacles, vertex
collisions, and edge swaps without relying on solver internals.
