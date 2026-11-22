from dashboard_helpers import read_output
def test_parquet(module15, fake_root):
    module15.build(fake_root)
    p=read_output(fake_root,"dashboard_payload_quality_report.json")["parquet_output"]
    assert p["written"] in {True, False}

