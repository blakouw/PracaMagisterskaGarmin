from .helpers11 import load_module


def test_urgency_factor_formula():
    module = load_module()
    assert module.urgency_factor(100) == 1.0
    assert module.urgency_factor(80) == 1.0
    assert module.urgency_factor(60) == 1.125
    assert module.urgency_factor(40) == 1.25
    assert module.urgency_factor(0) == 1.5
