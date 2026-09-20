from pathlib import Path
from dataclasses import replace

import pytest

from warehouse_mapf.movingai import (
    load_movingai_map,
    load_movingai_scen,
    problem_from_scenario,
    select_scenario_rows,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_map_and_scenario_parsing_converts_coordinates():
    grid = load_movingai_map(FIXTURES / "tiny.map")
    assert (grid.height, grid.width) == (4, 5)
    assert not grid.is_free((0, 2)) and not grid.is_free((1, 3))
    rows = load_movingai_scen(FIXTURES / "tiny.scen")
    assert rows[0].start == (0, 0)
    assert rows[0].goal == (3, 4)
    selected = select_scenario_rows(rows, grid, count=2)
    problem = problem_from_scenario(grid, selected)
    assert len(problem.agents) == 2


def test_random_selection_is_deterministic():
    grid = load_movingai_map(FIXTURES / "tiny.map")
    rows = load_movingai_scen(FIXTURES / "tiny.scen")
    first = select_scenario_rows(rows, grid, count=2, strategy="random", seed=7)
    second = select_scenario_rows(rows, grid, count=2, strategy="random", seed=7)
    assert [row.row_id for row in first] == [row.row_id for row in second]


def test_duplicate_starts_and_goals_are_not_selected_twice():
    grid = load_movingai_map(FIXTURES / "tiny.map")
    rows = load_movingai_scen(FIXTURES / "tiny.scen")
    duplicate = replace(rows[0], row_id=99)
    selected = select_scenario_rows([duplicate, *rows], grid, count=3)
    assert len({row.start for row in selected}) == 3
    assert len({row.goal for row in selected}) == 3


def test_invalid_map_and_scenario_are_rejected():
    with pytest.raises(ValueError, match="unsupported terrain"):
        load_movingai_map(FIXTURES / "bad_unknown.map")
    with pytest.raises(ValueError, match="expected 2 map rows"):
        load_movingai_map(FIXTURES / "bad_truncated.map")
    with pytest.raises(ValueError, match="version 1"):
        load_movingai_scen(FIXTURES / "bad_version.scen")


def test_dimension_and_blocked_endpoint_mismatch_are_rejected():
    grid = load_movingai_map(FIXTURES / "tiny.map")
    with pytest.raises(ValueError, match="dimensions"):
        select_scenario_rows(load_movingai_scen(FIXTURES / "wrong_dimensions.scen"), grid, count=1)
    with pytest.raises(ValueError, match="endpoint"):
        select_scenario_rows(load_movingai_scen(FIXTURES / "blocked.scen"), grid, count=1)
    with pytest.raises(ValueError, match="map name"):
        select_scenario_rows(
            load_movingai_scen(FIXTURES / "wrong_map_name.scen"), grid, count=1,
            expected_map_name="tiny.map",
        )
