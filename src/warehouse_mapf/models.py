"""Shared problem, solution, and constraint types."""

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .grid import GridMap

Position = tuple[int, int]


@dataclass(frozen=True)
class Agent:
    """An AGV with a unique identifier and fixed grid endpoints."""
    id: str
    start: Position
    goal: Position


@dataclass
class MAPFProblem:
    """A grid and the agents that must move on it."""
    grid: "GridMap"
    agents: list[Agent]


@dataclass
class Solution:
    """Solver output; success and collision-free validity are separate."""
    paths: dict[str, list[Position]] = field(default_factory=dict)
    success: bool = False
    runtime_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VertexConstraint:
    """Forbid an agent at a cell at an integer timestep."""
    agent: str
    time: int
    position: Position


@dataclass(frozen=True)
class EdgeConstraint:
    """Forbid source->target during the transition time->time+1."""
    agent: str
    time: int
    source: Position
    target: Position
