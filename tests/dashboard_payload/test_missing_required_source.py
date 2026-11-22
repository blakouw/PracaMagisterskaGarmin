import os
def test_missing_required_source(module15, fake_root):
    os.remove(fake_root/"data/pipeline/08_compute_load_metrics/load_metrics.json")
    assert module15.build(fake_root)[0] == 1

