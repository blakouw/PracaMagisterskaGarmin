import csv
import importlib.util
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "data_processing/activities.py"
@pytest.fixture
def module06():
    spec=importlib.util.spec_from_file_location('normalize_activities', MODULE_PATH)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod); return mod
def read_json(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def copy_policy(root:Path, mutate=None):
    (root/'config').mkdir(parents=True,exist_ok=True)
    policy=read_json(ROOT/'config'/'garmin_activity_normalization_v1.json')
    if mutate: mutate(policy)
    (root/'config'/'garmin_activity_normalization_v1.json').write_text(json.dumps(policy),encoding='utf-8')
    return policy
def write_activities_csv(root:Path, rows:list[dict]):
    d=root/'data'/'pipeline'/'03_trim_workbook'/'trimmed_sheets'; d.mkdir(parents=True,exist_ok=True)
    headers=['activityId','activityName','activityType','startTimeLocal','distance','duration','calories','averageSpeed','maxSpeed','averageHR','maxHR','avgPower','maxPower','elevationGain','elevationLoss','hrTimeInZone1','hrTimeInZone2','hrTimeInZone3','hrTimeInZone4','hrTimeInZone5','directWorkoutRpe','directWorkoutFeel']
    with (d/'Activities.csv').open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=headers); w.writeheader(); [w.writerow(r) for r in rows]
    manifest={'module_id':'03_trim_workbook','ready_for_next_module':True,'sheets':[{'sheet_name':'Activities','artifact_path':'data/pipeline/03_trim_workbook/trimmed_sheets/Activities.csv'}]}
    (d.parent/'trimmed_sheets_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
def base_row(**kw):
    r={'activityId':'100','activityName':'Morning Run','activityType':'running','startTimeLocal':'2026-05-22T07:14:00','distance':'10240','duration':'3140','calories':'712','averageSpeed':'3.5','maxSpeed':'5.0','averageHR':'148','maxHR':'169','avgPower':'271','maxPower':'402','elevationGain':'96','elevationLoss':'94','hrTimeInZone1':'220','hrTimeInZone2':'680','hrTimeInZone3':'1180','hrTimeInZone4':'920','hrTimeInZone5':'140'}
    r.update(kw); return r
def run(module06, root): return module06.execute(root=root)
def out(root): return root/'data'/'pipeline'/'06_normalize_activities'
