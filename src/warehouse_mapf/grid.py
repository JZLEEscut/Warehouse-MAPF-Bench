"""Grid representation using (row, column) coordinates."""

from dataclasses import dataclass, field
from .models import Position


@dataclass(frozen=True)
class GridMap:
    """A rectangular 4-neighbour map with fixed obstacles."""
    height: int
    width: int
    obstacles: frozenset[Position] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.height <= 0 or self.width <= 0:
            raise ValueError("grid dimensions must be positive")
        if any(not self.in_bounds(pos) for pos in self.obstacles):
            raise ValueError("obstacle outside grid")

    def in_bounds(self, position: Position) -> bool:
        """Return whether a position belongs to the grid."""
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width

    def is_free(self, position: Position) -> bool:
        """Return whether a position is in bounds and traversable."""
        return self.in_bounds(position) and position not in self.obstacles

    def neighbors(self, position: Position, include_wait: bool = False) -> list[Position]:
        """Return legal U, L, R, D neighbours and optionally WAIT."""
        row, col = position
        result = [(row - 1, col), (row, col - 1), (row, col + 1), (row + 1, col)]
        if include_wait:
            result.append(position)
        return [pos for pos in result if self.is_free(pos)]
