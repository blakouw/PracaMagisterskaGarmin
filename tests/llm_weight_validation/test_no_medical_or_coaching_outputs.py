from helpers import read_output
def test_no_forbidden_outputs(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    text=str(read_output(fake_root))
    assert "coach_message" not in text
    assert "medical_diagnosis" not in text
