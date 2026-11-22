import os
def test_missing_pws_weights(module13, fake_root):
    os.remove(fake_root/"data/pipeline/11_compute_pws_weights/pws_weights.json")
    assert module13.run(["--dry-run"], root=fake_root) == 1
