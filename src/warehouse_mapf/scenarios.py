"""Deterministic synthetic warehouse scenarios."""

from collections import deque
from random import Random
from .grid import GridMap
from .models import Agent, MAPFProblem, Position


def make_warehouse_grid(height: int = 18, width: int = 28) -> GridMap:
    """Build a connected rectangular shelf-and-aisle layout."""
    if height < 10 or width < 16:
        raise ValueError("warehouse grid needs at least 10x16 cells")
    obstacles: set[Position] = set()
    for row_start in range(2, height - 2, 4):
        for col_start in range(3, width - 2, 6):
            for row in range(row_start, min(row_start + 2, height - 1)):
                for col in range(col_start, min(col_start + 3, width - 1)):
                    obstacles.add((row, col))
    return GridMap(height, width, frozenset(obstacles))


def _connected_cells(grid: GridMap) -> list[Position]:
    free = [(row, col) for row in range(grid.height) for col in range(grid.width) if grid.is_free((row, col))]
    if not free:
        return []
    visited = {free[0]}
    queue: deque[Position] = deque([free[0]])
    while queue:
        for nxt in grid.neighbors(queue.popleft()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return sorted(visited)


def sample_problem(grid: GridMap, num_agents: int, seed: int) -> MAPFProblem:
    """Sample unique starts and goals reproducibly from one connected component."""
    cells = _connected_cells(grid)
    if num_agents * 2 > len(cells):
        raise ValueError("not enough free cells")
    rng = Random(seed)
    starts = rng.sample(cells, num_agents)
    goals = rng.sample([cell for cell in cells if cell not in starts], num_agents)
    return MAPFProblem(grid, [Agent(f"agv_{index:02d}", starts[index], goals[index]) for index in range(num_agents)])
