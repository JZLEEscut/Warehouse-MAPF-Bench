"""Exercise the real HTTP boundary and solver-to-replay contract."""

from http.server import ThreadingHTTPServer
import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from warehouse_mapf.web_demo import DemoHandler, solve_request


def test_live_results_distinguish_invalid_baseline_partial_failure_and_valid_plan():
    baseline = solve_request({"scenario": ["crossing"], "solver": ["independent_astar"]})
    assert baseline["success"] and not baseline["valid"] and baseline["conflicts"]
    failed = solve_request({"scenario": ["goal_hold"], "solver": ["pp_static"]})
    assert not failed["success"] and not failed["valid"]
    assert failed["sum_of_costs"] is None and len(failed["paths"]) == 1
    solved = solve_request({"scenario": ["goal_hold"], "solver": ["pp_longest_static"]})
    assert solved["valid"] and not solved["conflicts"]
    assert len(solved["paths"]) == len(solved["agents"]) == 2


def test_http_page_json_bad_requests_and_busy_response():
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/") as response:
            assert b'Planning Lab' in response.read()
            assert response.headers["Content-Type"].startswith("text/html")
        with urlopen(base + "/api/solve?scenario=crossing&solver=cbs_static") as response:
            assert json.load(response)["valid"]
        for path, status in (("/api/solve?agents=100", 400), ("/api/solve?solver=bad", 400),
                             ("/api/solve?scenario=unknown", 400),
                             ("/api/solve?seed=1&seed=2", 400), ("/missing", 404)):
            with pytest.raises(HTTPError) as exc:
                urlopen(base + path)
            assert exc.value.code == status
        with DemoHandler.solve_lock:
            with pytest.raises(HTTPError) as exc:
                urlopen(base + "/api/solve")
            assert exc.value.code == 429
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
