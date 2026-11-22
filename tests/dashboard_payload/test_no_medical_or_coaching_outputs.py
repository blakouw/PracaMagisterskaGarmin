from dashboard_helpers import read_output
def test_no_medical(module15, fake_root):
    module15.build(fake_root)
    text=str(read_output(fake_root))
    assert "coach_message" not in text
    assert read_output(fake_root)["disclosures"]["no_medical_diagnosis_generated"] is True


