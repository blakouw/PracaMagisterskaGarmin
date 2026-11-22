import os
def test_missing_deterministic_pws(module13, fake_root):
    os.remove(fake_root/"data/pipeline/12_compute_pws_score/pws_score.json")
    assert module13.run(["--dry-run"], root=fake_root) == 1
