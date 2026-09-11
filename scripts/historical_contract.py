"""Read the six-file task contract from the revision that produced a run.

This verifies historical integrity. Current-runtime compatibility remains a
separate audit; a matching historical hash does not authorize current reuse.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import subprocess


def task_contract_at_revision(root: Path, revision: str, task_paths: list[str]) -> str:
    root = Path(root)
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", revision + "^{commit}"], cwd=root,
        text=True, stderr=subprocess.DEVNULL,
    ).strip()

    def read(relative: str) -> bytes:
        return subprocess.check_output(
            ["git", "show", commit + ":" + relative], cwd=root,
            stderr=subprocess.DEVNULL,
        )

    contracts = []
    for task in dict.fromkeys(task_paths):
        directory = PurePosixPath(task)
        if directory.is_absolute() or ".." in directory.parts:
            raise ValueError("historical task path must be repository-relative")
        try:
            initial = read(task + "/frontier_eval/initial_program.txt").decode("utf-8").strip()
        except subprocess.CalledProcessError:
            continue
        initial_path = PurePosixPath(initial)
        if not initial or initial_path.is_absolute() or ".." in initial_path.parts:
            raise ValueError("historical initial program escapes the task")
        digest = hashlib.sha256()
        for relative in (
            "Task.md", initial, "verification/evaluator.py",
            "frontier_eval/metadata.yaml", "frontier_eval/constraints.txt",
            "frontier_eval/entrypoint.txt",
        ):
            digest.update(relative.encode("utf-8") + b"\0")
            digest.update(read(task + "/" + relative) + b"\0")
        contracts.append(digest.hexdigest())
    if not contracts:
        raise ValueError("task is absent from the recorded source revision")
    if len(set(contracts)) != 1:
        raise ValueError("historical task aliases have different contracts")
    return contracts[0]
