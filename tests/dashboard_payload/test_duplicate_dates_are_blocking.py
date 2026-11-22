import json
def test_duplicate_dates(module15, fake_root):
    p=fake_root/"data/pipeline/12_compute_pws_score/pws_score.json"
    data=json.loads(p.read_text()); data["records"].append(data["records"][0]); p.write_text(json.dumps(data))
    assert module15.build(fake_root)[0] == 1

