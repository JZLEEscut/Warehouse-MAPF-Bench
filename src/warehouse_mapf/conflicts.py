"""Vertex and edge-swap conflict detection."""

from dataclasses import dataclass
from typing import Literal
from .models import Position


@dataclass(frozen=True)
class Conflict:
    """A conflict between two paths at a stable timestep."""
    kind: Literal["vertex", "edge"]
    agent1: str
    agent2: str
    time: int
    position: Position | None = None
    edge1: tuple[Position, Position] | None = None
    edge2: tuple[Position, Position] | None = None


def position_at(path: list[Position], time: int) -> Position:
    """Read a path while holding its final goal after arrival."""
    if not path:
        raise ValueError("empty path")
    return path[min(time, len(path) - 1)]


def find_all_conflicts(paths: dict[str, list[Position]]) -> list[Conflict]:
    """Return all pairwise conflicts in chronological, stable agent order."""
    ids = sorted(paths)
    if len(ids) < 2:
        return []
    horizon = max(len(path) for path in paths.values()) - 1
    result: list[Conflict] = []
    for time in range(horizon + 1):
        for index, agent1 in enumerate(ids):
            for agent2 in ids[index + 1:]:
                p1 = position_at(paths[agent1], time)
                p2 = position_at(paths[agent2], time)
                if p1 == p2:
                    result.append(Conflict("vertex", agent1, agent2, time, position=p1))
                if time < horizon:
                    n1 = position_at(paths[agent1], time + 1)
                    n2 = position_at(paths[agent2], time + 1)
                    if p1 == n2 and p2 == n1 and p1 != p2:
                        result.append(Conflict("edge", agent1, agent2, time, edge1=(p1, n1), edge2=(p2, n2)))
    return result


def find_first_conflict(paths: dict[str, list[Position]]) -> Conflict | None:
    """Return the earliest deterministic conflict, if any."""
    conflicts = find_all_conflicts(paths)
    return conflicts[0] if conflicts else None
