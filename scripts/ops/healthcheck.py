from __future__ import annotations

import argparse
from pathlib import Path
import sys

import requests
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Ensure project root is importable when running as a script.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.database import SessionLocal
from src.scoring.config_schema import load_scoring_config


def check_database() -> tuple[bool, str]:
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return True, "database reachable"
    except SQLAlchemyError as exc:
        return False, f"database error: {exc}"
    finally:
        session.close()


def check_scoring_config() -> tuple[bool, str]:
    try:
        load_scoring_config()
        return True, "scoring config valid"
    except (FileNotFoundError, ValueError) as exc:
        return False, f"scoring config error: {exc}"


def check_http(url: str, timeout: float) -> tuple[bool, str]:
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"http ok ({response.status_code})"
        return False, f"http status {response.status_code}"
    except requests.RequestException as exc:
        return False, f"http error: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospect system healthcheck")
    parser.add_argument("--url", default="http://localhost:8000/healthz", help="Health endpoint URL")
    parser.add_argument("--timeout", type=float, default=3.0, help="HTTP timeout in seconds")
    parser.add_argument("--skip-http", action="store_true", help="Skip HTTP check")
    args = parser.parse_args()

    checks: list[tuple[str, tuple[bool, str]]] = [
        ("database", check_database()),
        ("scoring", check_scoring_config()),
    ]
    if not args.skip_http:
        checks.append(("http", check_http(args.url, args.timeout)))

    all_ok = True
    print("== HEALTHCHECK ==")
    for name, (ok, message) in checks:
        status = "OK" if ok else "FAIL"
        print(f"{name:<10} {status:<4} {message}")
        if not ok:
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
