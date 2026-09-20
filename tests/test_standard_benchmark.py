from pathlib import Path

from warehouse_mapf.standard_benchmark import build_movingai_instances


def test_standard_instance_identity_contains_selected_rows():
    fixtures = Path(__file__).parent / "fixtures"
    instances, selections = build_movingai_instances(
        fixtures / "tiny.map", fixtures / "tiny.scen", counts=[2], selection_seeds=[3],
    )
    assert len(instances) == 1
    assert instances[0].source == "movingai"
    assert instances[0].selection_row_ids
    assert "rows-" in instances[0].instance_id
    assert selections[0]["row_ids"]
