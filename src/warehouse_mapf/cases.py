"""Small, deterministic counterexamples for demonstrations and regression tests."""

from .grid import GridMap
from .models import Agent, MAPFProblem

CASE_DESCRIPTIONS = {
    "corridor": "窄通道会车：两台车需要利用中间的避让位。 / Passing bays in a narrow aisle.",
    "crossing": "交叉口冲突：独立最短路同时经过中心，需要等待或绕行。 / Intersection contention.",
    "goal_hold": "目标持续占用：先停在路口会堵住另一台车，优先级会改变结果。 / Goal holding and priority sensitivity.",
}


def make_case(name: str) -> MAPFProblem:
    if name == "corridor":
        height, width = 3, 7
        free = {(1, c) for c in range(7)} | {(0, 3), (2, 3)}
        agents = [Agent("A", (1, 0), (1, 6)), Agent("B", (1, 6), (1, 0))]
    elif name == "crossing":
        height, width = 3, 3
        free = {(r, c) for r in range(3) for c in range(3)}
        agents = [Agent("A", (1, 0), (1, 2)), Agent("B", (0, 1), (2, 1))]
    elif name == "goal_hold":
        height, width = 3, 5
        free = {(1, c) for c in range(5)} | {(0, 2), (2, 2)}
        agents = [Agent("A", (0, 2), (1, 2)), Agent("B", (1, 0), (1, 4))]
    else:
        raise ValueError(f"unknown case: {name}")
    obstacles = frozenset((r, c) for r in range(height) for c in range(width) if (r, c) not in free)
    return MAPFProblem(GridMap(height, width, obstacles), agents)
