"""Shared problem, solution, and constraint types."""

from dataclasses import dataclass, field
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .grid import GridMap

Position = tuple[int, int]
Outcome = Literal["solved", "timeout", "no_solution", "no_solution_within_limits", "error"]


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
    """Solver output with an explicit terminal outcome.

    ``success`` means a complete path set was returned before limits. It does
    not imply that the independently checked path set is valid.
    """
    paths: dict[str, list[Position]] = field(default_factory=dict)
    success: bool = False
    runtime_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    outcome: Outcome = "error"
    timed_out: bool = False

    def __post_init__(self) -> None:
        if self.timed_out != (self.outcome == "timeout"):
            raise ValueError("timed_out must be true exactly when outcome is 'timeout'")
        if self.success != (self.outcome == "solved"):
            raise ValueError("success must be true exactly when outcome is 'solved'")


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
