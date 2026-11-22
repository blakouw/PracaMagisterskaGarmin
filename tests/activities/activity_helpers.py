import importlib.util, json, shutil, sys, uuid, csv
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
MODULE_PATH=ROOT/'pipeline'/'06_normalize_activities'/'main.py'
@pytest.fixture
def case_root():
    root=ROOT/'.tmp_test'/'module06'/uuid.uuid4().hex
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    return root
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
def write_api(root:Path, aid='200', details=None, splits=None, fit=True, tcx=True):
    base=root/'data'/'pipeline'/'04_garmin_activity_ingest'/'activities'/aid; base.mkdir(parents=True,exist_ok=True)
    downloaded=[]
    if details is not None:
        (base/'details.json').write_text(json.dumps(details),encoding='utf-8'); downloaded.append({'artifact_type':'details_json','relative_path':f'data/pipeline/04_garmin_activity_ingest/activities/{aid}/details.json','status':'downloaded'})
    if splits is not None:
        (base/'splits.json').write_text(json.dumps(splits),encoding='utf-8'); downloaded.append({'artifact_type':'splits_json','relative_path':f'data/pipeline/04_garmin_activity_ingest/activities/{aid}/splits.json','status':'downloaded'})
    if fit:
        (base/'activity.fit').write_bytes(b'FIT'); downloaded.append({'artifact_type':'fit_file','relative_path':f'data/pipeline/04_garmin_activity_ingest/activities/{aid}/activity.fit','status':'downloaded'})
    if tcx:
        (base/'activity.tcx').write_text('<tcx/>',encoding='utf-8'); downloaded.append({'artifact_type':'tcx_file','relative_path':f'data/pipeline/04_garmin_activity_ingest/activities/{aid}/activity.tcx','status':'downloaded'})
    (base/'download_manifest.json').write_text(json.dumps({'activity_id':aid,'status':'downloaded','downloaded_artifacts':downloaded}),encoding='utf-8')
    manifest={'module_id':'04_garmin_activity_ingest','status':'completed','activities':[{'activity_id':aid,'status':'downloaded','manifest_path':f'data/pipeline/04_garmin_activity_ingest/activities/{aid}/download_manifest.json'}]}
    (root/'data'/'pipeline'/'04_garmin_activity_ingest').mkdir(parents=True,exist_ok=True)
    (root/'data'/'pipeline'/'04_garmin_activity_ingest'/'activity_ingest_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
def run(module06, root): return module06.execute(root=root)
def out(root): return root/'data'/'pipeline'/'06_normalize_activities'
def success_fixture(root): copy_policy(root); write_activities_csv(root,[base_row()])
