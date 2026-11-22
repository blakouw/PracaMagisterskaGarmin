from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def module_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def configure_api_import(root: Path) -> None:
    candidates = [
        root / "pipeline" / "17_local_api_server",
        Path(__file__).resolve().parents[1] / "17_local_api_server",
        Path(getattr(sys, "_MEIPASS", root)) / "17_local_api_server",
    ]
    for candidate in candidates:
        if candidate.is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


ROOT = module_root()
configure_api_import(ROOT)

from api_app import handle_get, load_snapshot  # noqa: E402


def safe_static_path(ui_root: Path, request_path: str) -> Path | None:
    path = unquote(urlparse(request_path).path)
    if path in {"", "/"}:
        return ui_root / "index.html"
    candidate = (ui_root / path.lstrip("/")).resolve()
    try:
        candidate.relative_to(ui_root.resolve())
    except ValueError:
        return None
    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.is_file():
        return candidate
    return ui_root / "index.html"


def create_handler(root: Path):
    ctx = load_snapshot(root, port=DEFAULT_PORT, verify_file_hashes=False)
    ui_root = root / "runtime" / "ui"

    class RuntimeHandler(BaseHTTPRequestHandler):
        server_version = "PersonalWellnessDashboard/1.0"

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _method_not_allowed(self) -> None:
            self._send_json(405, {"error": "method_not_allowed", "code": "METHOD_NOT_ALLOWED"})

        def do_POST(self) -> None:
            self._method_not_allowed()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/v1/"):
                query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                status, payload = handle_get(ctx, parsed.path, query)
                self._send_json(status, payload)
                return
            self._serve_static()

        def _serve_static(self) -> None:
            if not ui_root.is_dir():
                self._send_json(503, {"error": "ui_unavailable", "code": "PACKAGED_UI_ASSETS_MISSING"})
                return
            static_path = safe_static_path(ui_root, self.path)
            if static_path is None or not static_path.is_file():
                self._send_json(404, {"error": "not_found", "code": "STATIC_ASSET_NOT_FOUND"})
                return
            body = static_path.read_bytes()
            content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store" if static_path.name == "index.html" else "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)

    return RuntimeHandler


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the packaged local Personal Wellness Dashboard.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if os.environ.get("PWS_DASHBOARD_HOST") not in {None, "", DEFAULT_HOST}:
        print("Public host override is prohibited. This runtime binds only to 127.0.0.1.", file=sys.stderr)
        return 2
    handler = create_handler(ROOT)
    server = ThreadingHTTPServer((DEFAULT_HOST, DEFAULT_PORT), handler)
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/"
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    print(f"Personal Wellness Dashboard is running locally at {url}")
    print("Press Ctrl+C to stop. This runtime does not sync Garmin data or run the analytical pipeline.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
