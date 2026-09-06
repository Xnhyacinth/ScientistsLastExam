#!/usr/bin/env python3
"""Fetch hash-pinned MIPLIB solution assets for local offline evaluation.

The official solution pages do not state a separate per-solution license, so
these files are deliberately not redistributed in this candidate branch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(__file__).resolve().parent / "source_manifest.json"
MAX_ASSET_BYTES = 10 * 1024 * 1024


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assets() -> list[dict[str, str]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return list(manifest["external_solution_assets"])


def check_assets() -> list[str]:
    issues = []
    for artifact in assets():
        path = TASK_DIR / artifact["path"]
        if not path.is_file():
            issues.append(artifact["path"] + ": missing")
        elif _sha256(path) != artifact["sha256"]:
            issues.append(artifact["path"] + ": sha256 mismatch")
    return issues


def fetch_assets(force: bool = False) -> None:
    for artifact in assets():
        target = TASK_DIR / artifact["path"]
        if target.is_file() and _sha256(target) == artifact["sha256"]:
            continue
        if target.exists() and not force:
            raise RuntimeError(target.as_posix() + " exists with the wrong hash")
        target.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            artifact["source_url"],
            headers={"User-Agent": "ScientistsLastExam-MIPLIB-asset-fetch/1"},
        )
        temporary_name = None
        try:
            with urllib.request.urlopen(
                request, timeout=60
            ) as response, tempfile.NamedTemporaryFile(
                dir=str(target.parent), prefix=".download-", delete=False
            ) as temporary:
                temporary_name = temporary.name
                size = 0
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_ASSET_BYTES:
                        raise RuntimeError("solution asset exceeds the size cap")
                    temporary.write(chunk)
            temporary_path = Path(temporary_name)
            if _sha256(temporary_path) != artifact["sha256"]:
                raise RuntimeError("downloaded solution asset hash differs")
            os.replace(str(temporary_path), str(target))
            temporary_name = None
        finally:
            if temporary_name is not None:
                try:
                    Path(temporary_name).unlink()
                except FileNotFoundError:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not args.check:
        fetch_assets(force=args.force)
    issues = check_assets()
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("all four MIPLIB solution assets match the frozen hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
