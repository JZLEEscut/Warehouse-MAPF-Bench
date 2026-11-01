"""Portable experiment environment snapshots; no private paths or credentials."""

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
import hashlib
from pathlib import Path
import platform
import subprocess
import sys


def write_environment(destination: Path, parameters: dict) -> None:
    def git(*args: str) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=Path(__file__).resolve().parents[2],
                                           text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return "unavailable"

    dependencies = {}
    for package in ("warehouse-mapf-bench", "matplotlib", "pandas", "pillow", "pytest"):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = "not installed"
    document = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_worktree_status": git("status", "--porcelain", "--untracked-files=no"),
        "python": platform.python_version(), "system": platform.system(),
        "system_release": platform.release(), "machine": platform.machine(),
        "processor": platform.processor(), "dependencies": dependencies,
        "argv": [Path(sys.argv[0]).name, *sys.argv[1:]], "parameters": parameters,
        "source_sha256": {
            path.relative_to(Path(__file__).parent).as_posix(): hashlib.sha256(
                path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            for path in sorted(Path(__file__).parent.rglob("*"))
            if path.suffix in (".py", ".html")
        },
        "timing": "perf_counter wall time; includes preprocessing and solver validation; excludes reporting/rendering",
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "environment.json").write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
