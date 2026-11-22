import json
def test_not_ready(module15, fake_root):
    p=fake_root/"data/pipeline/09_compute_readiness/readiness.json"
    data=json.loads(p.read_text()); data["ready_for_next_module"]=False; p.write_text(json.dumps(data))
    assert module15.build(fake_root)[0] == 1

