from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.historical_contract import task_contract_at_revision


class HistoricalContractTests(unittest.TestCase):
    def test_recorded_hash_survives_current_edits_but_rejects_bad_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            task = "benchmarks/Fixture/Example"
            files = {
                "Task.md": b"synthetic test fixture, not scientific evidence\n",
                "solution.py": b"def solve(): return 0\n",
                "verification/evaluator.py": b"def evaluate(candidate): return candidate()\n",
                "frontier_eval/metadata.yaml": b"task: Example\n",
                "frontier_eval/constraints.txt": b"fixture\n",
                "frontier_eval/entrypoint.txt": b"solve\n",
            }
            expected = hashlib.sha256()
            for relative, payload in files.items():
                path = root / task / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                expected.update(relative.encode() + b"\0" + payload + b"\0")
            (root / task / "frontier_eval/initial_program.txt").write_text("solution.py\n")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "-qm", "fixture"], cwd=root, check=True)
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            self.assertEqual(task_contract_at_revision(root, revision, [task]), expected.hexdigest())
            (root / task / "Task.md").write_text("changed current contract\n")
            self.assertEqual(task_contract_at_revision(root, revision, [task]), expected.hexdigest())
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "-qm", "changed"], cwd=root, check=True)
            self.assertNotEqual(task_contract_at_revision(root, "HEAD", [task]), expected.hexdigest())
            with self.assertRaises(ValueError):
                task_contract_at_revision(root, revision, ["benchmarks/Missing/Example"])
            with self.assertRaises(ValueError):
                task_contract_at_revision(root, revision, ["../outside"])
            with self.assertRaises(subprocess.CalledProcessError):
                task_contract_at_revision(root, "missing-commit", [task])
