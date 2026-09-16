from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import write_json_atomic


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def manifest_path(figure_dir: Path) -> Path:
    return figure_dir / ".funfig" / "manifest.json"


def write_manifest(figure_dir: Path, value: dict[str, Any]) -> None:
    write_json_atomic(manifest_path(figure_dir), value)

