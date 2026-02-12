from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Codex prompt from diagnostics findings.")
    parser.add_argument("--analysis", required=True, help="Path to diagnostics analysis JSON.")
    parser.add_argument("--output", required=True, help="Path to write prompt text.")
    args = parser.parse_args()

    analysis_path = Path(args.analysis)
    output_path = Path(args.output)

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    findings = analysis.get("findings", [])
    recommendations = analysis.get("recommendations", [])

    prompt_lines = [
        "You are fixing the current repository based on diagnostics findings.",
        "Goal: resolve all blocking errors and warnings from the report, then rerun validations.",
        "",
        "Diagnostics findings:",
    ]
    if not findings:
        prompt_lines.append("- No findings were reported. Verify and improve robustness where possible.")
    else:
        for finding in findings[:50]:
            severity = finding.get("severity", "warning").upper()
            kind = finding.get("kind", "unknown")
            name = finding.get("name", "unnamed")
            message = finding.get("message", "No message.")
            prompt_lines.append(f"- [{severity}] {kind}::{name} - {message}")
            stdout_tail = finding.get("stdout_tail", [])
            stderr_tail = finding.get("stderr_tail", [])
            if stdout_tail:
                prompt_lines.append("  stdout tail:")
                for line in stdout_tail[-5:]:
                    prompt_lines.append(f"  {line}")
            if stderr_tail:
                prompt_lines.append("  stderr tail:")
                for line in stderr_tail[-5:]:
                    prompt_lines.append(f"  {line}")

    prompt_lines.append("")
    prompt_lines.append("Recommendations:")
    for recommendation in recommendations:
        prompt_lines.append(f"- {recommendation}")

    prompt_lines.extend(
        [
            "",
            "Required output:",
            "1. Apply concrete code fixes in the repository.",
            "2. Run backend tests and frontend build.",
            "3. Summarize what was fixed and residual risks.",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
