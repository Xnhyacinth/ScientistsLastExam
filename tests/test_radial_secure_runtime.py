from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
import sysconfig
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from _sandbox_tools import skip_unless_sandbox

from sle.evaluate import INVALID_SCORE, evaluate_candidate
from sle.secure_eval import read_candidate_packages
from sle.spec import load_task_spec


ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "benchmarks" / "Physics" / "RadialVelocityPlanets"


class RadialVelocityPackageContractTests(unittest.TestCase):
    def test_candidate_package_version_mismatch_fails_closed(self):
        with patch("sle.secure_eval.importlib.metadata.version", return_value="7.0.0"):
            with self.assertRaisesRegex(
                RuntimeError,
                "trusted candidate package 'astropy' has version 7.0.0, expected 5.2.2",
            ):
                read_candidate_packages(TASK_DIR)


@skip_unless_sandbox("bwrap")
class RadialVelocitySecureRuntimeTests(unittest.TestCase):
    def test_baseline_can_import_the_pinned_astropy_in_the_candidate_sandbox(self):
        try:
            astropy_version = importlib.metadata.version("astropy")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("the trusted test interpreter does not provide astropy")
        if astropy_version != "5.2.2":
            self.skipTest("the trusted test interpreter does not provide astropy 5.2.2")

        spec = load_task_spec(TASK_DIR)
        with patch.dict(
            os.environ,
            {"FRONTIER_SCIENCE_TRUSTED_PYTHON": sys.executable},
        ):
            result = evaluate_candidate(
                spec,
                TASK_DIR / "solution.py",
                timeout_s=180,
            )

        self.assertNotEqual(result["combined_score"], INVALID_SCORE, result)
        self.assertNotIn("infrastructure_failure", result, result)
        self.assertEqual(result["valid"], 1.0, result)

    def test_oracle_setup_checks_the_pinned_astropy_version(self):
        try:
            astropy_version = importlib.metadata.version("astropy")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("the trusted test interpreter does not provide astropy")
        if astropy_version != "5.2.2":
            self.skipTest("the trusted test interpreter does not provide astropy 5.2.2")

        completed = subprocess.run(
            ["bash", "scripts/setup_oracle_env.sh", "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "ORACLE_PYTHON": sys.executable},
        )

        self.assertRegex(completed.stdout, r"(?m)^\s*astropy\s+present\s+5\.2\.2$")

    def test_candidate_gets_the_trusted_abi_without_the_oracle_virtualenv(self):
        try:
            astropy_version = importlib.metadata.version("astropy")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("the trusted test interpreter does not provide astropy")
        if astropy_version != "5.2.2":
            self.skipTest("the trusted test interpreter does not provide astropy 5.2.2")

        trusted_soabi = sysconfig.get_config_var("SOABI")
        trusted_prefix = str(Path(sys.prefix).resolve())
        source = """
            def detect_planets(_observation):
                import astropy
                import os
                import sys
                import sysconfig

                if sys.executable != "/runtime/bin/python":
                    raise RuntimeError("wrong candidate executable")
                if sysconfig.get_config_var("SOABI") != %r:
                    raise RuntimeError("wrong candidate ABI")
                if astropy.__version__ != "5.2.2":
                    raise RuntimeError("wrong astropy version")
                if os.path.exists(%r):
                    raise RuntimeError("trusted virtualenv is visible")
                try:
                    import pymatching
                except ImportError:
                    pass
                else:
                    raise RuntimeError("unrequested oracle package is visible")
                return {"abstain": True}
        """ % (trusted_soabi, trusted_prefix)
        spec = load_task_spec(TASK_DIR)
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate.py"
            candidate.write_text(textwrap.dedent(source), encoding="utf-8")
            with patch.dict(
                os.environ,
                {"FRONTIER_SCIENCE_TRUSTED_PYTHON": sys.executable},
            ):
                result = evaluate_candidate(spec, candidate, timeout_s=180)

        self.assertNotIn("infrastructure_failure", result, result)
        self.assertEqual(result["valid"], 1.0, result)


if __name__ == "__main__":
    unittest.main()
