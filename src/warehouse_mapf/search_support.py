"""Per-solve search instrumentation and deadline-aware static distances."""

from collections import deque
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Callable, Literal

from .grid import GridMap
from .models import Position

Heuristic = Literal["manhattan", "static"]


class SearchTimeout(RuntimeError):
    """The shared search deadline expired, including preprocessing."""


@dataclass
class SearchStats:
    low_level_calls: int = 0
    low_level_expanded: int = 0
    precompute_ms: float = 0.0
    precompute_cells: int = 0
    distance_cache_hits: int = 0

    def metadata(self) -> dict[str, int | float]:
        return asdict(self)


class DistanceCache:
    """Cache reverse BFS by goal on ONE immutable grid, for ONE solver call."""

    def __init__(self, grid: GridMap, stats: SearchStats):
        self.grid = grid
        self.stats = stats
        self._tables: dict[Position, dict[Position, int]] = {}

    def distances(self, goal: Position, *, deadline: float | None = None,
                  clock: Callable[[], float] = perf_counter) -> dict[Position, int]:
        if deadline is not None and clock() >= deadline:
            raise SearchTimeout("distance preprocessing deadline exceeded")
        if goal in self._tables:
            self.stats.distance_cache_hits += 1
            return self._tables[goal]
        started = perf_counter()
        table = {goal: 0} if self.grid.is_free(goal) else {}
        queue = deque(table)
        try:
            while queue:
                if deadline is not None and clock() >= deadline:
                    raise SearchTimeout("distance preprocessing deadline exceeded")
                current = queue.popleft()
                self.stats.precompute_cells += 1
                for nxt in self.grid.neighbors(current):
                    if nxt not in table:
                        table[nxt] = table[current] + 1
                        queue.append(nxt)
        finally:
            self.stats.precompute_ms += (perf_counter() - started) * 1000
        self._tables[goal] = table
        return table
