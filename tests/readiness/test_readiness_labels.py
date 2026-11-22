from .helpers09 import load_module


def test_readiness_label_boundaries():
    module = load_module()
    assert module.readiness_label(39.99) == ("low", "niska")
    assert module.readiness_label(40) == ("reduced", "obnizona")
    assert module.readiness_label(60) == ("moderate", "umiarkowana")
    assert module.readiness_label(80) == ("high", "wysoka")
    assert module.readiness_label(None) == ("insufficient_data", "insufficient_data")
