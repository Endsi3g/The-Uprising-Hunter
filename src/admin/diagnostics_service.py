from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from ..core.logging import get_logger


logger = get_logger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
QA_DIR = ROOT_DIR / "scripts" / "qa"
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "qa"
RUNNER_SCRIPT = QA_DIR / "run_intelligent_diagnostics.ps1"
DIAGNOSTICS_FILE = ARTIFACTS_DIR / "latest_diagnostics.json"
AUTOFIX_FILE = ARTIFACTS_DIR / "latest_autofix.json"


def _ensure_dirs() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_latest_diagnostics() -> dict[str, Any]:
    _ensure_dirs()
    payload = _load_json(DIAGNOSTICS_FILE)
    if payload is None:
        return {
            "available": False,
            "artifact": str(DIAGNOSTICS_FILE),
            "detail": "No diagnostics artifact available yet.",
        }
    payload["available"] = True
    payload["artifact"] = str(DIAGNOSTICS_FILE)
    return payload


def get_latest_autofix() -> dict[str, Any]:
    _ensure_dirs()
    payload = _load_json(AUTOFIX_FILE)
    if payload is None:
        return {
            "available": False,
            "artifact": str(AUTOFIX_FILE),
            "detail": "No autofix artifact available yet.",
        }
    payload["available"] = True
    payload["artifact"] = str(AUTOFIX_FILE)
    return payload


def run_intelligent_diagnostics(*, auto_fix: bool = False) -> dict[str, Any]:
    _ensure_dirs()
    if not RUNNER_SCRIPT.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing diagnostics script: {RUNNER_SCRIPT}",
        )

    started_at = _now_iso()
    started = time.perf_counter()
    args = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(RUNNER_SCRIPT),
        "-WriteArtifactsOnly",
    ]
    if auto_fix:
        args.append("-AutoFix")

    process = subprocess.run(  # noqa: S603
        args,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    duration = round(time.perf_counter() - started, 3)
    finished_at = _now_iso()

    stdout_tail = (process.stdout or "").splitlines()[-40:]
    stderr_tail = (process.stderr or "").splitlines()[-40:]
    output_file = AUTOFIX_FILE if auto_fix else DIAGNOSTICS_FILE
    artifact_payload = _load_json(output_file) or {}

    payload = {
        "ok": process.returncode == 0,
        "return_code": process.returncode,
        "auto_fix": auto_fix,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "artifact": str(output_file),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "artifact_payload": artifact_payload,
    }

    logger.info(
        "Intelligent diagnostics executed.",
        extra={
            "auto_fix": auto_fix,
            "return_code": process.returncode,
            "duration_seconds": duration,
        },
    )
    return payload
