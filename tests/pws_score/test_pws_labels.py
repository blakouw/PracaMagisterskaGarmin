from .helpers12 import load_module


def test_pws_labels():
    module = load_module()
    assert module.label_for(39.99) == ("low", "niski")
    assert module.label_for(40) == ("reduced", "obnizony")
    assert module.label_for(60) == ("balanced", "stabilny")
    assert module.label_for(80) == ("strong", "wysoki")
    assert module.label_for(None) == ("insufficient_data", "insufficient_data")
