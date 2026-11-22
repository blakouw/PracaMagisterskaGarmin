import csv
def test_csv(module15, fake_root):
    module15.build(fake_root)
    p=fake_root/"data/pipeline/15_build_dashboard_payload/dashboard_time_series.csv"
    rows=list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows)==3
    assert rows[2]["pws_deterministic"] == ""

