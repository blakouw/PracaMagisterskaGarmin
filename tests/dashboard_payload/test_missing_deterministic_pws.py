import os
def test_missing_deterministic_pws(module15, fake_root):
    os.remove(fake_root/"data/pipeline/12_compute_pws_score/pws_score.json")
    assert module15.build(fake_root)[0] == 1

