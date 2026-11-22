from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


class GarminClientAdapter:
    """Thin local adapter around the optional garminconnect package."""

    @staticmethod
    def dependency_available() -> bool:
        return importlib.util.find_spec("garminconnect") is not None

    def __init__(self, tokenstore_dir: Path):
        module = importlib.import_module("garminconnect")
        self._garmin_class = getattr(module, "Garmin")
        self._client = self._garmin_class()
        self._client.login(str(tokenstore_dir))

    def get_activity_details(self, activity_id: str) -> Any:
        return self._client.get_activity_details(int(activity_id))

    def get_activity_splits(self, activity_id: str) -> Any:
        return self._client.get_activity_splits(int(activity_id))

    def download_activity_fit(self, activity_id: str) -> bytes:
        fmt = getattr(self._garmin_class.ActivityDownloadFormat, "ORIGINAL")
        payload = self._client.download_activity(int(activity_id), dl_fmt=fmt)
        return payload if isinstance(payload, bytes) else bytes(payload)

    def download_activity_tcx(self, activity_id: str) -> bytes:
        fmt = getattr(self._garmin_class.ActivityDownloadFormat, "TCX")
        payload = self._client.download_activity(int(activity_id), dl_fmt=fmt)
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            return payload.encode("utf-8")
        return bytes(payload)
