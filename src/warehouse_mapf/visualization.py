"""Matplotlib animation for solver trajectories."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import ListedColormap
from .conflicts import position_at
from .models import MAPFProblem, Position


def save_animation(problem: MAPFProblem, paths: dict[str, list[Position]], output: str | Path, *, fps: int = 3) -> Path:
    """Render real solver paths as a GIF."""
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = [[1 if (row, col) in problem.grid.obstacles else 0 for col in range(problem.grid.width)] for row in range(problem.grid.height)]
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    ax.imshow(image, cmap=ListedColormap(["#f7f4ea", "#3c4a58"]), interpolation="nearest")
    colors = plt.get_cmap("tab10")
    ids = [agent.id for agent in problem.agents]
    goals = [agent.goal for agent in problem.agents]
    ax.scatter([pos[1] for pos in goals], [pos[0] for pos in goals], marker="x", s=65, c="black", linewidths=1.1)
    dots = [ax.plot([], [], "o", color=colors(index % 10), markersize=7)[0] for index in range(len(ids))]
    ax.set(xlabel="column", ylabel="row")
    ax.set_xticks(range(0, problem.grid.width, 2))
    ax.set_yticks(range(0, problem.grid.height, 2))
    ax.grid(color="#d7d2c7", linewidth=0.4)
    title = ax.set_title("Warehouse MAPF — timestep 0")

    def update(frame: int):
        for dot, agent_id in zip(dots, ids):
            row, col = position_at(paths[agent_id], frame)
            dot.set_data([col], [row])
        title.set_text(f"Warehouse MAPF — timestep {frame}")
        return [*dots, title]

    animation = FuncAnimation(fig, update, frames=range(max(len(path) for path in paths.values())), interval=1000 // fps)
    animation.save(destination, writer=PillowWriter(fps=fps), dpi=100)
    plt.close(fig)
    return destination
