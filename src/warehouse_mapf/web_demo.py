"""Loopback-only demo server, using the standard library and existing solvers."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from .astar import solve_independent
from .cases import CASE_DESCRIPTIONS, make_case
from .improvement_study import VARIANTS, solve_variant
from .replay import replay_payload
from .scenarios import make_warehouse_grid, sample_problem


def solve_request(query: dict[str, list[str]]) -> dict:
    def value(key: str, default: str) -> str:
        values = query.get(key, [default])
        if len(values) != 1:
            raise ValueError(f"multiple values for {key}")
        return values[0]

    scenario = value("scenario", "goal_hold")
    solver = value("solver", "cbs_static")
    agents = int(value("agents", "8"))
    seed = int(value("seed", "17"))
    if not 1 <= agents <= 25 or not 0 <= seed <= 1_000_000:
        raise ValueError("agents must be 1–25; seed must be 0–1000000")
    if solver not in (*VARIANTS, "independent_astar"):
        raise ValueError("unknown solver")
    if scenario == "warehouse":
        problem = sample_problem(make_warehouse_grid(), agents, seed)
        description = "合成仓储 / Synthetic warehouse"
    else:
        problem = make_case(scenario)
        description = CASE_DESCRIPTIONS[scenario]
    solution = solve_independent(problem) if solver == "independent_astar" else solve_variant(problem, solver, 2.0)
    return {**replay_payload(problem, solution), "scenario": scenario, "description": description,
            "solver": solver, "seed": seed, "limit_seconds": None if solver == "independent_astar" else 2.0}


class DemoHandler(BaseHTTPRequestHandler):
    solve_lock = Lock()

    def respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if url.path == "/":
            body = files("warehouse_mapf").joinpath("web/index.html").read_bytes()
            self.respond(200, body, "text/html; charset=utf-8")
            return
        if url.path != "/api/solve":
            self.respond(404, b"Not found", "text/plain")
            return
        if not self.solve_lock.acquire(blocking=False):
            self.respond(429, b'{"error":"Solver busy; try again shortly"}', "application/json")
            return
        try:
            result = solve_request(parse_qs(url.query, keep_blank_values=True))
        except (ValueError, KeyError) as exc:
            self.respond(400, json.dumps({"error": str(exc)}).encode(), "application/json")
        except Exception:
            self.log_error("unexpected solver error")
            self.respond(500, b'{"error":"Unexpected solver error"}', "application/json")
        else:
            self.respond(200, json.dumps(result, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        finally:
            self.solve_lock.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DemoHandler)
    print(f"Warehouse MAPF demo: http://127.0.0.1:{server.server_port} — Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
