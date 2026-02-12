from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_command_failures(commands_payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for entry in commands_payload.get("commands", []):
        if int(entry.get("exit_code", 0)) != 0:
            failures.append(
                {
                    "kind": "command",
                    "name": entry.get("name"),
                    "severity": "error",
                    "message": f"Command '{entry.get('name')}' failed with exit code {entry.get('exit_code')}.",
                    "stdout_tail": entry.get("stdout_tail", [])[-20:],
                    "stderr_tail": entry.get("stderr_tail", [])[-20:],
                }
            )
    return failures


def _extract_scrape_failures(scrape_payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for issue in scrape_payload.get("issues", []):
        failures.append(
            {
                "kind": "scrape",
                "name": issue.get("scope"),
                "severity": issue.get("severity", "warning"),
                "message": issue.get("message", "Unknown scrape issue."),
            }
        )
    return failures


def _recommendations(failures: list[dict[str, Any]]) -> list[str]:
    recs: list[str] = []
    has_pytest = any(f.get("name") == "pytest" for f in failures)
    has_build = any(f.get("name") == "frontend_build" for f in failures)
    has_smoke = any(f.get("name") == "localhost_smoke" for f in failures)
    has_scrape = any(f.get("kind") == "scrape" for f in failures)
    if has_pytest:
        recs.append("Fix backend test regressions first (`python -m pytest -q`).")
    if has_build:
        recs.append("Fix frontend compile/build errors (`cd admin-dashboard && npm run build`).")
    if has_smoke:
        recs.append("Investigate API runtime issues from localhost smoke (`test_localhost_all_features.ps1`).")
    if has_scrape:
        recs.append("Check page/API routes flagged by scraper for runtime errors.")
    if not recs:
        recs.append("No blocking issue detected. Keep monitoring with periodic diagnostics.")
    return recs


def _markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Intelligent QA Report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- OK: `{payload['ok']}`",
        f"- Error count: `{payload['error_count']}`",
        f"- Warning count: `{payload['warning_count']}`",
        "",
        "## Findings",
    ]
    if not payload["findings"]:
        lines.append("- No issues detected.")
    else:
        for finding in payload["findings"]:
            lines.append(
                f"- [{finding.get('severity', 'warning').upper()}] {finding.get('kind')}::{finding.get('name')}: {finding.get('message')}"
            )

    lines.extend(["", "## Recommendations"])
    for item in payload["recommendations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze diagnostics outputs and aggregate findings.")
    parser.add_argument("--commands", required=True, help="Path to command results JSON.")
    parser.add_argument("--scrape", required=True, help="Path to scrape results JSON.")
    parser.add_argument("--output-json", required=True, help="Path to aggregated JSON output.")
    parser.add_argument("--output-md", required=True, help="Path to markdown output.")
    args = parser.parse_args()

    commands_payload = _read_json(Path(args.commands))
    scrape_payload = _read_json(Path(args.scrape))
    findings = _extract_command_failures(commands_payload) + _extract_scrape_failures(scrape_payload)

    error_count = sum(1 for finding in findings if finding.get("severity") == "error")
    warning_count = sum(1 for finding in findings if finding.get("severity") != "error")
    recommendations = _recommendations(findings)
    output_payload = {
        "generated_at": _now_iso(),
        "ok": error_count == 0,
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": findings,
        "recommendations": recommendations,
        "command_summary": commands_payload.get("commands", []),
        "scrape_summary": {
            "issue_count": scrape_payload.get("issue_count", 0),
            "error_count": scrape_payload.get("error_count", 0),
            "warning_count": scrape_payload.get("warning_count", 0),
        },
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    output_md.write_text(_markdown_report(output_payload), encoding="utf-8")

    print(json.dumps(output_payload, indent=2))
    return 0 if output_payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
