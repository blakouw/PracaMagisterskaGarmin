
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "17_local_api_server"
POLICY_VERSION = "dashboard_snapshot_api_policy_v1"
SNAPSHOT_MODULE_ID = "16_persist_local_snapshot"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_LIMIT = 10000
REQUIRED_CURRENT_FILES = [
    "dashboard_payload.json",
    "dashboard_time_series.csv",
    "dashboard_payload_schema.json",
    "dashboard_payload_quality_report.json",
    "dashboard_payload_lineage.json",
    "snapshot_manifest.json",
    "snapshot_source_hashes.json",
    "snapshot_status.json",
]
JSON_FILES = [
    "dashboard_payload.json",
    "dashboard_payload_schema.json",
    "dashboard_payload_quality_report.json",
    "dashboard_payload_lineage.json",
    "snapshot_manifest.json",
    "snapshot_source_hashes.json",
    "snapshot_status.json",
]
GET_ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/snapshot/status",
    "/api/v1/snapshot/manifest",
    "/api/v1/dashboard",
    "/api/v1/dashboard/current-state",
    "/api/v1/dashboard/time-series",
    "/api/v1/dashboard/quality",
    "/api/v1/dashboard/disclosures",
]
POST_ENDPOINTS = [
    "/api/v1/dashboard/chat",
]
LOCAL_LLM_HOSTS = {"127.0.0.1", "localhost"}
CHAT_MAX_MESSAGE_CHARS = 2000
CHAT_MAX_HISTORY_MESSAGES = 8


@dataclass
class SnapshotContext:
    root: Path
    port: int = DEFAULT_PORT
    validation_status: str = "degraded_snapshot_unavailable"
    snapshot_available: bool = False
    snapshot_id: str | None = None
    latest_data_date: str | None = None
    payload: dict[str, Any] | None = None
    status: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    hashes: dict[str, Any] | None = None
    quality: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=lambda: ["This API is local-only and read-only and is not approved for public or network exposure."])
    file_hashes_reverified_on_startup: bool = False

    @property
    def ready(self) -> bool:
        return self.snapshot_available and self.validation_status == "valid"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def current_dir(root: Path) -> Path:
    return root / "data" / "published" / "dashboard_snapshots" / "current"


def policy_path(root: Path) -> Path:
    return root / "config" / "dashboard_snapshot_api_policy_v1.json"


def validate_api_policy(policy: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"code": "DASHBOARD_SNAPSHOT_API_POLICY_INVALID", "message": "Invalid policy version."})
    runtime = policy.get("runtime", {})
    if runtime.get("default_host") != DEFAULT_HOST or runtime.get("allow_host_override") is not False:
        errors.append({"code": "PUBLIC_HOST_BINDING_PROHIBITED", "message": "API must bind only to 127.0.0.1 and disallow host override."})
    if runtime.get("approved_for_public_exposure") is not False or runtime.get("approved_for_lan_exposure") is not False:
        errors.append({"code": "DASHBOARD_SNAPSHOT_API_POLICY_INVALID", "message": "Public or LAN exposure must not be approved."})
    http_policy = policy.get("http_policy", {})
    allowed_methods = set(http_policy.get("allowed_methods", []))
    if http_policy.get("read_only") is not True or allowed_methods - {"GET", "POST"} or "GET" not in allowed_methods:
        errors.append({"code": "WRITE_ENDPOINT_PROHIBITED", "message": "Only GET and the approved ephemeral chat POST are allowed."})
    if "POST" in allowed_methods and http_policy.get("allowed_post_endpoints") != POST_ENDPOINTS:
        errors.append({"code": "WRITE_ENDPOINT_PROHIBITED", "message": "POST is allowed only for the local ephemeral dashboard chat endpoint."})
    if any(method in set(http_policy.get("disallowed_methods", [])) for method in {"PUT", "PATCH", "DELETE"}) is False:
        errors.append({"code": "WRITE_ENDPOINT_PROHIBITED", "message": "PUT, PATCH and DELETE must remain disallowed."})
    cors = policy.get("cors_policy", {})
    if cors.get("enabled_by_default") is not False or cors.get("allow_wildcard_origins") is not False:
        errors.append({"code": "CORS_WILDCARD_PROHIBITED", "message": "Wildcard/default CORS is prohibited."})
    return errors


def verify_hashes(current: Path, hashes: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    for item in hashes.get("files", []):
        filename = item.get("filename")
        if not filename or item.get("present") is False:
            continue
        path = current / filename
        if not path.is_file():
            errors.append({"code": "CURRENT_SNAPSHOT_REQUIRED_FILE_NOT_FOUND", "message": f"Snapshot file is missing: {filename}"})
            continue
        expected = item.get("snapshot_sha256") or item.get("source_sha256")
        if expected and sha256_file(path) != expected:
            errors.append({"code": "CURRENT_SNAPSHOT_HASH_STATUS_INVALID", "message": f"Hash mismatch for {filename}"})
    return not errors, errors


def load_snapshot(root: Path, port: int = DEFAULT_PORT, verify_file_hashes: bool = False) -> SnapshotContext:
    ctx = SnapshotContext(root=root, port=port, file_hashes_reverified_on_startup=verify_file_hashes)
    try:
        policy = read_json(policy_path(root))
    except FileNotFoundError:
        ctx.errors.append({"code": "DASHBOARD_SNAPSHOT_API_POLICY_NOT_FOUND", "message": "API policy is missing."})
        return ctx
    except json.JSONDecodeError:
        ctx.errors.append({"code": "DASHBOARD_SNAPSHOT_API_POLICY_INVALID", "message": "API policy JSON is invalid."})
        return ctx
    policy_errors = validate_api_policy(policy)
    if policy_errors:
        ctx.validation_status = "blocked_invalid_api_policy"
        ctx.errors.extend(policy_errors)
        return ctx

    current = current_dir(root)
    if not current.is_dir():
        ctx.errors.append({"code": "CURRENT_SNAPSHOT_DIRECTORY_NOT_FOUND", "message": "Current snapshot directory is unavailable."})
        return ctx
    missing = [name for name in REQUIRED_CURRENT_FILES if not (current / name).is_file()]
    if missing:
        ctx.errors.append({"code": "CURRENT_SNAPSHOT_REQUIRED_FILE_NOT_FOUND", "message": f"Missing current snapshot files: {missing}"})
        return ctx
    loaded: dict[str, Any] = {}
    try:
        for name in JSON_FILES:
            loaded[name] = read_json(current / name)
    except json.JSONDecodeError:
        ctx.errors.append({"code": "CURRENT_SNAPSHOT_JSON_INVALID", "message": "A current snapshot JSON file is invalid."})
        return ctx

    payload = loaded["dashboard_payload.json"]
    status = loaded["snapshot_status.json"]
    manifest = loaded["snapshot_manifest.json"]
    hashes = loaded["snapshot_source_hashes.json"]
    ctx.payload = payload
    ctx.status = status
    ctx.manifest = manifest
    ctx.hashes = hashes
    ctx.quality = loaded["dashboard_payload_quality_report.json"]
    ctx.snapshot_id = status.get("snapshot_id")
    ctx.latest_data_date = status.get("latest_data_date")

    if status.get("payload_ready") is not True:
        ctx.validation_status = "blocked_invalid_snapshot_contract"
        ctx.errors.append({"code": "CURRENT_SNAPSHOT_NOT_READY", "message": "Snapshot status payload_ready is not true."})
    if not isinstance(status.get("primary_pws"), dict) or status["primary_pws"].get("score_type") != "deterministic":
        ctx.validation_status = "blocked_invalid_primary_score_contract"
        ctx.errors.append({"code": "PRIMARY_SCORE_NOT_DETERMINISTIC", "message": "Snapshot status primary PWS is not deterministic."})
    for section in ["metadata", "current_state", "time_series", "quality_and_coverage", "disclosures"]:
        if section not in payload:
            ctx.validation_status = "blocked_invalid_snapshot_contract"
            ctx.errors.append({"code": "CURRENT_SNAPSHOT_NOT_READY", "message": f"Dashboard payload missing section {section}."})
    primary = payload.get("current_state", {}).get("primary_pws", {})
    if primary.get("score_type") != "deterministic":
        ctx.validation_status = "blocked_invalid_primary_score_contract"
        ctx.errors.append({"code": "PRIMARY_SCORE_NOT_DETERMINISTIC", "message": "Dashboard primary PWS is not deterministic."})
    assisted = payload.get("current_state", {}).get("optional_assisted_pws", {})
    if isinstance(assisted, dict) and assisted.get("available") is True:
        if assisted.get("score_type") != "llm_assisted" or assisted.get("must_not_replace_primary_score") is not True:
            ctx.validation_status = "blocked_assisted_score_contract_violation"
            ctx.errors.append({"code": "ASSISTED_VARIANT_CONTRACT_VIOLATION", "message": "Optional assisted PWS violates the snapshot API contract."})
    manifest_primary = manifest.get("primary_score_policy", {})
    if manifest_primary.get("score_type") != "deterministic" or manifest_primary.get("preserved_without_modification") is not True:
        ctx.errors.append({"code": "PRIMARY_SCORE_NOT_DETERMINISTIC", "message": "Snapshot manifest does not confirm deterministic primary score."})
    if hashes.get("all_required_hashes_verified") is not True:
        ctx.errors.append({"code": "CURRENT_SNAPSHOT_HASH_STATUS_INVALID", "message": "Published hash verification status is not valid."})
    if verify_file_hashes:
        ok, hash_errors = verify_hashes(current, hashes)
        if not ok:
            ctx.errors.extend(hash_errors)
    if ctx.errors:
        if ctx.validation_status == "degraded_snapshot_unavailable":
            ctx.validation_status = "blocked_invalid_snapshot_contract"
        return ctx
    ctx.validation_status = "valid"
    ctx.snapshot_available = True
    return ctx

def health_payload(ctx: SnapshotContext) -> dict[str, Any]:
    base = {"service": "dashboard_snapshot_api", "api_version": "v1", "local_only": True, "read_only": True}
    if ctx.ready:
        status = ctx.status or {}
        primary = status.get("primary_pws", {})
        assisted = status.get("optional_assisted_pws", {})
        return base | {
            "status": "ok",
            "snapshot_available": True,
            "snapshot_id": ctx.snapshot_id,
            "latest_data_date": ctx.latest_data_date,
            "primary_score_type": primary.get("score_type"),
            "optional_assisted_score_available": bool(assisted.get("available")),
        }
    code = ctx.errors[0]["code"] if ctx.errors else "CURRENT_SNAPSHOT_NOT_AVAILABLE"
    return base | {"status": "degraded", "snapshot_available": False, "snapshot_error_code": code}


def require_snapshot(ctx: SnapshotContext) -> None:
    if not ctx.ready:
        code = ctx.errors[0]["code"] if ctx.errors else "CURRENT_SNAPSHOT_NOT_AVAILABLE"
        raise ApiError(503, {"error": "snapshot_unavailable", "code": code})


class ApiError(Exception):
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("code", "api_error"))
        self.status_code = status_code
        self.payload = payload


def parse_query_date(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    if not valid_date(value):
        raise ApiError(400, {"error": "invalid_query_parameter", "code": "TIME_SERIES_QUERY_DATE_INVALID", "parameter": name})
    return value


def parse_limit(value: str | int | None) -> int | None:
    if value is None:
        return None
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ApiError(400, {"error": "invalid_query_parameter", "code": "TIME_SERIES_QUERY_LIMIT_INVALID", "parameter": "limit"}) from exc
    if limit < 1 or limit > MAX_LIMIT:
        raise ApiError(400, {"error": "invalid_query_parameter", "code": "TIME_SERIES_QUERY_LIMIT_INVALID", "parameter": "limit"})
    return limit


def filtered_time_series(ctx: SnapshotContext, date_from: str | None = None, date_to: str | None = None, limit: str | int | None = None) -> dict[str, Any]:
    require_snapshot(ctx)
    from_date = parse_query_date("date_from", date_from)
    to_date = parse_query_date("date_to", date_to)
    parsed_limit = parse_limit(limit)
    records = list((ctx.payload or {}).get("time_series", []))
    if from_date:
        records = [item for item in records if isinstance(item.get("date"), str) and item["date"] >= from_date]
    if to_date:
        records = [item for item in records if isinstance(item.get("date"), str) and item["date"] <= to_date]
    records = sorted(records, key=lambda item: item.get("date") or "")
    if parsed_limit is not None:
        records = records[-parsed_limit:]
        records = sorted(records, key=lambda item: item.get("date") or "")
    return {"snapshot_id": ctx.snapshot_id, "filters": {"date_from": from_date, "date_to": to_date, "limit": parsed_limit}, "records_count": len(records), "records": records}


def load_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def llm_policy(ctx: SnapshotContext) -> dict[str, Any]:
    path = ctx.root / "config" / "llm_policy_v1.json"
    try:
        policy = read_json(path)
    except FileNotFoundError as exc:
        raise ApiError(503, {"error": "llm_chat_unavailable", "code": "LLM_POLICY_NOT_FOUND"}) from exc
    except json.JSONDecodeError as exc:
        raise ApiError(503, {"error": "llm_chat_unavailable", "code": "LLM_POLICY_INVALID"}) from exc
    endpoint = str(policy.get("endpoint") or "")
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in LOCAL_LLM_HOSTS:
        raise ApiError(503, {"error": "llm_chat_unavailable", "code": "LLM_CHAT_ENDPOINT_NOT_LOCAL"})
    if not policy.get("model"):
        raise ApiError(503, {"error": "llm_chat_unavailable", "code": "LLM_CHAT_MODEL_NOT_CONFIGURED"})
    return policy


def conversation_prompt(ctx: SnapshotContext) -> str:
    prompt = load_text(ctx.root / "docs" / "llm_prompt_engineering" / "prompts" / "user_conversation_startup_prompt_v1.md")
    if prompt:
        return prompt
    return (
        "You are a local dashboard conversation assistant. Explain only already computed local dashboard data. "
        "Do not recompute metrics, call Garmin, run the pipeline, diagnose medical conditions or prescribe training."
    )


def chat_context(ctx: SnapshotContext) -> dict[str, Any]:
    require_snapshot(ctx)
    payload = ctx.payload or {}
    current = payload.get("current_state", {})
    primary = current.get("primary_pws", {})
    assisted = current.get("optional_assisted_pws", {})
    readiness = current.get("readiness", {})
    components = current.get("pws_components", {})
    weights = current.get("pws_weights", {})
    load_metrics = current.get("load_metrics", {})
    coverage = current.get("coverage", {})
    quality = payload.get("quality_and_coverage", {})
    return {
        "snapshot_id": ctx.snapshot_id,
        "latest_data_date": ctx.latest_data_date,
        "current_date": current.get("date"),
        "primary_pws": primary,
        "optional_assisted_pws": assisted,
        "readiness": readiness,
        "pws_components": components,
        "pws_weights": weights,
        "load_metrics": load_metrics,
        "coverage": coverage,
        "quality_summary": {
            "records_count": quality.get("records_count"),
            "coverage_tiers": quality.get("coverage_tiers"),
            "presentation_availability": quality.get("presentation_availability"),
        },
        "disclosures": payload.get("disclosures", {}),
    }


def clean_chat_message(value: Any, field: str = "message") -> str:
    if not isinstance(value, str):
        raise ApiError(400, {"error": "invalid_chat_request", "code": "CHAT_MESSAGE_INVALID", "field": field})
    value = value.strip()
    if not value or len(value) > CHAT_MAX_MESSAGE_CHARS:
        raise ApiError(400, {"error": "invalid_chat_request", "code": "CHAT_MESSAGE_INVALID", "field": field})
    return value


def clean_chat_history(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ApiError(400, {"error": "invalid_chat_request", "code": "CHAT_HISTORY_INVALID"})
    cleaned: list[dict[str, str]] = []
    for item in value[-CHAT_MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            raise ApiError(400, {"error": "invalid_chat_request", "code": "CHAT_HISTORY_INVALID"})
        cleaned.append({"role": item["role"], "content": clean_chat_message(item.get("content"), "history.content")})
    return cleaned


def build_chat_messages(ctx: SnapshotContext, body: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    message = clean_chat_message(body.get("message"))
    history = clean_chat_history(body.get("history"))
    context = chat_context(ctx)
    system = (
        f"{conversation_prompt(ctx)}\n\n"
        "Use the following local dashboard context as already-read tool output. "
        "Do not request or invent additional tools.\n"
        f"LOCAL_DASHBOARD_CONTEXT_JSON={json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"
    )
    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": message}]
    return messages, context


def extract_llm_answer(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ApiError(502, {"error": "llm_chat_failed", "code": "LLM_CHAT_RESPONSE_INVALID"})
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ApiError(502, {"error": "llm_chat_failed", "code": "LLM_CHAT_RESPONSE_INVALID"})
    return content.strip()


def complete_chat(ctx: SnapshotContext, body: dict[str, Any], llm_client: Any | None = None) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ApiError(400, {"error": "invalid_chat_request", "code": "CHAT_REQUEST_INVALID"})
    policy = llm_policy(ctx)
    messages, context = build_chat_messages(ctx, body)
    if llm_client is not None:
        answer = llm_client(messages=messages, context=context, policy=policy)
        if not isinstance(answer, str) or not answer.strip():
            raise ApiError(502, {"error": "llm_chat_failed", "code": "LLM_CHAT_RESPONSE_INVALID"})
        answer_text = answer.strip()
    else:
        api_key_name = policy.get("api_key_environment_variable")
        api_key = os.environ.get(api_key_name, "") if isinstance(api_key_name, str) else ""
        request_payload = {
            "model": policy.get("model"),
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 600,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            str(policy["endpoint"]),
            data=json.dumps(request_payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=int(policy.get("timeout_seconds", 60))) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ApiError(502, {"error": "llm_chat_failed", "code": "LLM_CHAT_REQUEST_FAILED"}) from exc
        answer_text = extract_llm_answer(response_payload)
    return {
        "snapshot_id": ctx.snapshot_id,
        "latest_data_date": ctx.latest_data_date,
        "answer": answer_text,
        "model": policy.get("model"),
        "provider": policy.get("provider"),
        "tools_used": [
            "dashboard_current_state",
            "dashboard_quality",
            "dashboard_disclosures",
        ],
        "llm_called": True,
        "persisted": False,
        "snapshot_modified": False,
        "pipeline_triggered": False,
        "forbidden_action_confirmation": {
            "garmin_api_called": False,
            "pipeline_triggered": False,
            "snapshot_modified": False,
            "medical_diagnosis_generated": False,
            "training_prescription_generated": False,
        },
    }


def handle_post(ctx: SnapshotContext, path: str, body: dict[str, Any] | None = None, llm_client: Any | None = None) -> tuple[int, dict[str, Any]]:
    try:
        if path == "/api/v1/dashboard/chat":
            require_snapshot(ctx)
            return 200, complete_chat(ctx, body or {}, llm_client=llm_client)
        return 404, {"error": "not_found", "code": "RESOURCE_NOT_FOUND"}
    except ApiError as exc:
        return exc.status_code, exc.payload


def handle_get(ctx: SnapshotContext, path: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    query = query or {}
    try:
        if path == "/api/v1/health":
            return 200, health_payload(ctx)
        if path == "/api/v1/snapshot/status":
            require_snapshot(ctx)
            return 200, ctx.status or {}
        if path == "/api/v1/snapshot/manifest":
            require_snapshot(ctx)
            return 200, ctx.manifest or {}
        if path == "/api/v1/dashboard":
            require_snapshot(ctx)
            return 200, ctx.payload or {}
        if path == "/api/v1/dashboard/current-state":
            require_snapshot(ctx)
            return 200, (ctx.payload or {}).get("current_state", {})
        if path == "/api/v1/dashboard/time-series":
            return 200, filtered_time_series(ctx, query.get("date_from"), query.get("date_to"), query.get("limit"))
        if path == "/api/v1/dashboard/quality":
            require_snapshot(ctx)
            return 200, (ctx.payload or {}).get("quality_and_coverage", {})
        if path == "/api/v1/dashboard/disclosures":
            require_snapshot(ctx)
            return 200, (ctx.payload or {}).get("disclosures", {})
        return 404, {"error": "not_found", "code": "RESOURCE_NOT_FOUND"}
    except ApiError as exc:
        return exc.status_code, exc.payload


def create_fastapi_app(ctx: SnapshotContext):
    try:
        from fastapi import FastAPI, Query, Request
        from fastapi.responses import JSONResponse
        globals()["Request"] = Request
    except ImportError as exc:
        raise RuntimeError("FastAPI is not installed. Install requirements.txt before serving the API.") from exc

    app = FastAPI(title="Local Dashboard Snapshot API", version="1.0.0", docs_url="/docs", redoc_url=None)

    def response(path: str, **query: Any):
        status_code, payload = handle_get(ctx, path, query)
        return JSONResponse(status_code=status_code, content=payload)

    def post_response(path: str, body: dict[str, Any]):
        status_code, payload = handle_post(ctx, path, body)
        return JSONResponse(status_code=status_code, content=payload)

    @app.get("/api/v1/health")
    def health():
        return response("/api/v1/health")

    @app.get("/api/v1/snapshot/status")
    def snapshot_status_endpoint():
        return response("/api/v1/snapshot/status")

    @app.get("/api/v1/snapshot/manifest")
    def snapshot_manifest_endpoint():
        return response("/api/v1/snapshot/manifest")

    @app.get("/api/v1/dashboard")
    def dashboard_endpoint():
        return response("/api/v1/dashboard")

    @app.get("/api/v1/dashboard/current-state")
    def current_state_endpoint():
        return response("/api/v1/dashboard/current-state")

    @app.get("/api/v1/dashboard/time-series")
    def time_series_endpoint(date_from: str | None = None, date_to: str | None = None, limit: int | None = Query(default=None)):
        return response("/api/v1/dashboard/time-series", date_from=date_from, date_to=date_to, limit=limit)

    @app.get("/api/v1/dashboard/quality")
    def quality_endpoint():
        return response("/api/v1/dashboard/quality")

    @app.get("/api/v1/dashboard/disclosures")
    def disclosures_endpoint():
        return response("/api/v1/dashboard/disclosures")

    @app.post("/api/v1/dashboard/chat")
    async def dashboard_chat_endpoint(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        return post_response("/api/v1/dashboard/chat", body)

    return app
