"""Pure metrics for path dictionaries."""

from .conflicts import find_all_conflicts
from .models import Position


def sum_of_costs(paths: dict[str, list[Position]]) -> int:
    """Return total movement/wait cost."""
    return sum(len(path) - 1 for path in paths.values())


def makespan(paths: dict[str, list[Position]]) -> int:
    """Return the longest individual path cost."""
    return max((len(path) - 1 for path in paths.values()), default=0)


def count_conflicts(paths: dict[str, list[Position]]) -> int:
    """Count all vertex and edge conflicts."""
    return len(find_all_conflicts(paths))
