"""Replay frozen solutions with the patched native MIPLIB solution checker.

This is a qualification utility, not the runtime oracle.  The official
checker historically returns process status zero even when a feasibility
check fails, so acceptance is determined from its three printed check flags.
"""
from __future__ import annotations

import gzip
import re
import subprocess
import tempfile
from pathlib import Path

LINEAR_TOLERANCE = "1e-6"
INTEGRALITY_TOLERANCE = "1e-5"
PASS_LINE = re.compile(
    r"^Check SOL: Integrality 1 Constraints 1 Objective 1$", re.MULTILINE
)


def checker_accepted(returncode: int, stdout: str) -> bool:
    return bool(
        returncode == 0
        and "Read MPS: 1" in stdout
        and "Read SOL: 1" in stdout
        and PASS_LINE.search(stdout)
    )


def run_checker(
    checker: Path,
    mps_path: Path,
    compressed_solution_path: Path,
) -> subprocess.CompletedProcess[str]:
    checker = Path(checker).resolve()
    mps_path = Path(mps_path).resolve()
    compressed_solution_path = Path(compressed_solution_path).resolve()
    if not checker.is_file() or not mps_path.is_file() or not (
        compressed_solution_path.is_file()
    ):
        raise FileNotFoundError("checker replay input is missing")
    with tempfile.TemporaryDirectory(prefix="miplib_checker_replay_") as tmp:
        solution_path = Path(tmp) / "candidate.sol"
        with gzip.open(compressed_solution_path, "rb") as source:
            solution_path.write_bytes(source.read())
        return subprocess.run(
            [
                str(checker),
                str(mps_path),
                str(solution_path),
                LINEAR_TOLERANCE,
                INTEGRALITY_TOLERANCE,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
