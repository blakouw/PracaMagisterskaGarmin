from .helpers08 import load_module


def test_acwr_zone_boundaries():
    module = load_module()
    assert module.zone_for(0.79)["zone_id"] == "underload"
    assert module.zone_for(0.8)["zone_id"] == "optimal"
    assert module.zone_for(1.3)["zone_id"] == "optimal"
    assert module.zone_for(1.31)["zone_id"] == "caution"
    assert module.zone_for(1.5)["zone_id"] == "caution"
    assert module.zone_for(1.51)["zone_id"] == "risk"
