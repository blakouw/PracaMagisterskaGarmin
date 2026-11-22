import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "04_garmin_activity_ingest" / "main.py"
MODULE_DIR = ROOT / "pipeline" / "04_garmin_activity_ingest"
sys.path.insert(0, str(MODULE_DIR))


@pytest.fixture
def case_root() -> Path:
    root = ROOT / ".tmp_test" / "module04" / uuid.uuid4().hex
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


@pytest.fixture
def module04():
    spec = importlib.util.spec_from_file_location("garmin_activity_ingest", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def public_config() -> dict:
    return read_json(ROOT / "config" / "garmin_activity_ingest_v1.json")


def write_config(root: Path, **overrides) -> dict:
    config = public_config()
    for key, value in overrides.items():
        config[key] = value
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "garmin_activity_ingest_v1.json").write_text(json.dumps(config), encoding="utf-8")
    return config


def write_tokenstore(root: Path, valid: bool = True, secret_prefix: str = "TEST") -> None:
    token_dir = root / "data" / "local_secrets" / "garmin_tokenstore"
    token_dir.mkdir(parents=True, exist_ok=True)
    if valid:
        oauth1 = {"oauth_token": f"{secret_prefix}_OAUTH1", "oauth_token_secret": f"{secret_prefix}_OAUTH1_SECRET"}
        oauth2 = {"access_token": f"{secret_prefix}_ACCESS", "refresh_token": f"{secret_prefix}_REFRESH"}
    else:
        oauth1 = {"oauth_token": ""}
        oauth2 = {"access_token": ""}
    (token_dir / "oauth1_token.json").write_text(json.dumps(oauth1), encoding="utf-8")
    (token_dir / "oauth2_token.json").write_text(json.dumps(oauth2), encoding="utf-8")


def write_activities_csv(root: Path, rows: list[dict[str, str]]) -> None:
    artifact_dir = root / "data" / "pipeline" / "03_trim_workbook"
    csv_dir = artifact_dir / "trimmed_sheets"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "Activities.csv"
    headers = ["activityId", "activityName"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(headers) + "\n")
        for row in rows:
            handle.write(f"{row.get('activityId', '')},{row.get('activityName', '')}\n")
    manifest = {
        "module_id": "03_trim_workbook",
        "status": "trimmed",
        "sheets": [{"sheet_name": "Activities", "artifact_path": "data/pipeline/03_trim_workbook/trimmed_sheets/Activities.csv"}],
        "ready_for_next_module": True,
    }
    (artifact_dir / "trimmed_sheets_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class FakeGarminAdapter:
    def __init__(self, tokenstore_dir: Path):
        self.tokenstore_dir = tokenstore_dir

    def get_activity_details(self, activity_id: str):
        return {"activityId": activity_id, "source": "mock"}

    def get_activity_splits(self, activity_id: str):
        return [{"activityId": activity_id, "split": 1}]

    def download_activity_fit(self, activity_id: str) -> bytes:
        return b"FITDATA"

    def download_activity_tcx(self, activity_id: str) -> bytes:
        return b"<TrainingCenterDatabase />"


class PartialFailureAdapter(FakeGarminAdapter):
    def download_activity_fit(self, activity_id: str) -> bytes:
        if activity_id == "200":
            raise RuntimeError("mock fit failure")
        return b"FITDATA"


def run_module(module04, root: Path, dependency=True, adapter=FakeGarminAdapter) -> int:
    return module04.execute(root=root, dependency_available=lambda: dependency, adapter_factory=adapter)


def artifact_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / "04_garmin_activity_ingest"
