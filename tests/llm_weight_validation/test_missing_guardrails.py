import os
def test_missing_guardrails(module13, fake_root):
    os.remove(fake_root/"data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json")
    assert module13.run(["--dry-run"], root=fake_root) == 1
