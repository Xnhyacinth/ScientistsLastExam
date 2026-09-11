#!/usr/bin/env python3
"""Report which pytest checks actually executed, including missing required checks.

This summarizes JUnit execution evidence; it does not certify scientific results.
Public CI may report unavailable historical runs. A benchmark-host replay can use
--required-tests to require those specific checks to execute and pass.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize(junit: Path, required_tests: list[str] | None = None) -> dict:
    tree = ET.parse(junit)
    cases = list(tree.getroot().iter("testcase"))
    rows = []
    seen = set()
    issues = []
    for case in cases:
        identity = "%s::%s" % (case.get("classname", ""), case.get("name", ""))
        if identity in seen:
            issues.append("duplicate test result: " + identity)
        seen.add(identity)
        status, reason = "passed", ""
        for tag, outcome in (("error", "error"), ("failure", "failed"), ("skipped", "skipped")):
            child = case.find(tag)
            if child is not None:
                status = outcome
                reason = child.get("message") or (child.text or "").strip()
                break
        rows.append({"test": identity, "status": status, "reason": reason})
    required = sorted(set(required_tests or []))
    by_id = {row["test"]: row for row in rows}
    required_results = []
    for identity in required:
        row = by_id.get(identity, {"test": identity, "status": "not_collected", "reason": "required check absent from JUnit"})
        required_results.append(row)
    counts = Counter(row["status"] for row in rows)
    if not cases:
        issues.append("JUnit contains no test cases")
    failed_requirements = [row for row in required_results if row["status"] != "passed"]
    passed = bool(cases and not issues and not failed_requirements
                  and counts["failed"] == 0 and counts["error"] == 0)
    return {
        "schema_version": 1,
        "evidence_scope": "TEST_EXECUTION_COVERAGE_ONLY",
        "junit": str(junit),
        "counts": {key: counts[key] for key in ("passed", "failed", "error", "skipped")},
        "collected_count": len(cases),
        "executed_count": sum(counts[key] for key in ("passed", "failed", "error")),
        "coverage_complete": bool(cases and not counts["skipped"] and not failed_requirements and not issues),
        "required_tests": required_results,
        "issues": issues,
        "tests": rows,
        "passed": passed,
    }


def markdown(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "Test execution coverage", "",
        "Passed: {passed}; failed: {failed}; errors: {error}; skipped: {skipped}.".format(**counts),
        "Executed: %s / %s collected checks." % (report["executed_count"], report["collected_count"]),
        "Coverage complete: %s. Skipped checks have not verified their evidence." % str(report["coverage_complete"]).lower(),
    ]
    missing = [row for row in report["required_tests"] if row["status"] != "passed"]
    if missing:
        lines.extend(["", "Required checks not passed:", ""])
        lines.extend("- `%s`: %s" % (row["test"], row["status"]) for row in missing)
    skipped = [row for row in report["tests"] if row["status"] == "skipped"]
    if skipped:
        lines.extend(["", "Skipped checks (first 20; full list in the JSON artifact):", ""])
        for row in skipped[:20]:
            reason = row["reason"].replace("\n", " ")[:240]
            lines.append("- `%s`: %s" % (row["test"], reason))
    if report["issues"]:
        lines.extend(["", "Report issues:", ""])
        lines.extend("- " + issue for issue in report["issues"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--required-tests", type=Path, help="JSON list of classname::test-name checks that must execute and pass")
    args = parser.parse_args(argv)
    required = json.loads(args.required_tests.read_text()) if args.required_tests else []
    if not isinstance(required, list) or any(not isinstance(item, str) or not item for item in required):
        parser.error("--required-tests must contain a JSON list of nonempty test identities")
    try:
        report = summarize(args.junit, required)
    except (OSError, ET.ParseError) as exc:
        parser.exit(2, "cannot read JUnit execution evidence: %s\n" % exc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rendered = markdown(report)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
