from app.engine import LegitFlowEngine
from app.models import CTEType


def test_engine_emits_supported_ctes_and_lineage():
    engine = LegitFlowEngine(seed=204)
    seen = set()
    parent_links = 0
    for _ in range(80):
        event, parents = engine.next_event()
        seen.add(event.cte_type)
        if parents:
            parent_links += 1
    assert CTEType.HARVESTING in seen
    assert CTEType.SHIPPING in seen
    assert CTEType.RECEIVING in seen
    assert parent_links > 0


def test_location_gln_lookup():
    engine = LegitFlowEngine(seed=204)
    assert engine.location_gln("Valley Fresh Farms") == "0850000001001"
