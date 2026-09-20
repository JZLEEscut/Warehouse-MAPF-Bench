"""Strict Moving AI ``.map`` and version-1 ``.scen`` input support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random

from .grid import GridMap
from .models import Agent, MAPFProblem, Position

TRAVERSABLE_TERRAIN = frozenset({".", "G", "S"})
BLOCKED_TERRAIN = frozenset({"@", "T", "O", "W"})


@dataclass(frozen=True)
class MovingAIScenarioRow:
    """One scenario row with coordinates converted to project row/column order."""

    row_id: int
    bucket: int
    map_name: str
    width: int
    height: int
    start: Position
    goal: Position
    optimal_length: float


def load_movingai_map(path: str | Path) -> GridMap:
    """Parse a Moving AI map, rejecting malformed headers and unknown terrain."""
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    if len(lines) < 5:
        raise ValueError(f"{source}: truncated Moving AI map")
    if not lines[0].lower().startswith("type "):
        raise ValueError(f"{source}: expected 'type' header")
    try:
        height_key, height_text = lines[1].split(maxsplit=1)
        width_key, width_text = lines[2].split(maxsplit=1)
        height, width = int(height_text), int(width_text)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{source}: invalid height/width header") from exc
    if height_key.lower() != "height" or width_key.lower() != "width" or lines[3].strip().lower() != "map":
        raise ValueError(f"{source}: expected height, width, then map headers")
    rows = lines[4:]
    if len(rows) != height:
        raise ValueError(f"{source}: expected {height} map rows, got {len(rows)}")
    obstacles: set[Position] = set()
    for row_index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"{source}: row {row_index} has width {len(row)}, expected {width}")
        for col_index, terrain in enumerate(row):
            if terrain in BLOCKED_TERRAIN:
                obstacles.add((row_index, col_index))
            elif terrain not in TRAVERSABLE_TERRAIN:
                raise ValueError(f"{source}: unsupported terrain {terrain!r} at ({row_index}, {col_index})")
    return GridMap(height, width, frozenset(obstacles))


def load_movingai_scen(path: str | Path) -> list[MovingAIScenarioRow]:
    """Parse Moving AI version-1 scenarios and convert ``(x, y)`` to ``(row, col)``."""
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip().lower() != "version 1":
        raise ValueError(f"{source}: expected 'version 1' scenario header")
    rows: list[MovingAIScenarioRow] = []
    for row_id, line in enumerate(lines[1:]):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 9:
            raise ValueError(f"{source}: scenario row {row_id} has {len(fields)} fields, expected 9")
        try:
            bucket = int(fields[0])
            map_name = fields[1]
            width, height = int(fields[2]), int(fields[3])
            start_x, start_y = int(fields[4]), int(fields[5])
            goal_x, goal_y = int(fields[6]), int(fields[7])
            optimal_length = float(fields[8])
        except ValueError as exc:
            raise ValueError(f"{source}: invalid numeric value in scenario row {row_id}") from exc
        rows.append(MovingAIScenarioRow(
            row_id, bucket, map_name, width, height,
            (start_y, start_x), (goal_y, goal_x), optimal_length,
        ))
    if not rows:
        raise ValueError(f"{source}: no scenario rows")
    return rows


def select_scenario_rows(
    rows: list[MovingAIScenarioRow],
    grid: GridMap,
    *,
    count: int,
    strategy: str = "first",
    seed: int = 0,
    expected_map_name: str | None = None,
) -> list[MovingAIScenarioRow]:
    """Select deterministic rows with unique starts/goals after strict validation."""
    if count <= 0:
        raise ValueError("count must be positive")
    for row in rows:
        if expected_map_name is not None and Path(row.map_name).name != Path(expected_map_name).name:
            raise ValueError(f"scenario row {row.row_id}: map name does not match {expected_map_name}")
        if (row.width, row.height) != (grid.width, grid.height):
            raise ValueError(f"scenario row {row.row_id}: dimensions do not match map")
        if not grid.is_free(row.start) or not grid.is_free(row.goal):
            raise ValueError(f"scenario row {row.row_id}: endpoint is blocked or out of bounds")
    candidates = list(rows)
    if strategy == "random":
        Random(seed).shuffle(candidates)
    elif strategy != "first":
        raise ValueError("selection strategy must be 'first' or 'random'")
    selected: list[MovingAIScenarioRow] = []
    starts: set[Position] = set()
    goals: set[Position] = set()
    for row in candidates:
        if row.start in starts or row.goal in goals:
            continue
        selected.append(row)
        starts.add(row.start)
        goals.add(row.goal)
        if len(selected) == count:
            return selected
    raise ValueError(f"only {len(selected)} rows satisfy unique start/goal requirements; requested {count}")


def problem_from_scenario(
    grid: GridMap,
    rows: list[MovingAIScenarioRow],
    *,
    expected_map_name: str | None = None,
) -> MAPFProblem:
    """Construct a MAPF problem from already selected and validated rows."""
    selected = select_scenario_rows(
        rows, grid, count=len(rows), strategy="first", expected_map_name=expected_map_name,
    )
    return MAPFProblem(grid, [Agent(f"row_{row.row_id}", row.start, row.goal) for row in selected])
