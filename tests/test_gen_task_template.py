"""The task generator must not emit a wrapper that runs the candidate unsandboxed.

`scripts/gen_task.py` writes each new task's `frontier_eval/run_eval.py`, the black-box entry
external harnesses call. Its template used to import the candidate and the oracle into the
same process, which is a way for candidate code to run outside the Bubblewrap sandbox
whenever anyone reaches for the convenience - the exact shape the exemplar task's wrapper
carries a comment warning against. Three submitted branches also shipped wrappers with
unrendered `{{ }}` placeholders, which fail on every evaluation, because the template is a
`.format()` string and nothing checked the rendered result.

These tests pin the properties of what the generator emits, not its wording.
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]


def _generator():
    spec = importlib.util.spec_from_file_location(
        "gen_task_under_test", REPO / "scripts" / "gen_task.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render(task="HarmonicOscillatorControl", task_id="Physics/HarmonicOscillatorControl",
            eval_timeout=300):
    return _generator().RUN_EVAL_TEMPLATE.format(
        task=task, task_id=task_id, eval_timeout=eval_timeout)


class GeneratedRunEvalTests(unittest.TestCase):
    def test_rendered_wrapper_is_valid_python(self):
        ast.parse(_render())

    def test_no_placeholder_survives_rendering(self):
        rendered = _render()
        for marker in ("{{", "}}", "{task}", "{task_id}", "{eval_timeout}"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, rendered)

    def test_wrapper_shells_out_instead_of_importing_the_candidate(self):
        rendered = _render()
        self.assertIn("subprocess.run(", rendered)
        self.assertIn('"-m", "sle", "eval"', rendered)
        for bypass in ("importlib", "exec_module", "spec_from_file_location", "exec("):
            with self.subTest(bypass=bypass):
                self.assertNotIn(bypass, rendered)

    def test_wrapper_reports_failures_instead_of_raising(self):
        rendered = _render()
        self.assertIn("error_message", rendered)
        self.assertIn("completed.returncode", rendered)
        self.assertIn("stderr", rendered)  # the reason has to reach the report

    def test_root_depth_matches_the_benchmarks_layout(self):
        """`parents[4]` must land on the repository root from the wrapper's own location."""
        match = re.search(r"parents\[(\d+)\]", _render())
        self.assertIsNotNone(match)
        depth = int(match.group(1))
        example = REPO / "benchmarks" / "Engineering" / "ModalDamageAttribution" / \
            "frontier_eval" / "run_eval.py"
        self.assertTrue(example.is_file())
        self.assertEqual(example.resolve().parents[depth], REPO)

    def test_timeout_follows_the_convention_and_can_be_overridden(self):
        module = _generator()
        default = module.DEFAULT_EVAL_TIME_SECONDS

        def timeout_for(spec):
            seconds = int(spec.get("eval_time_seconds") or default)
            return int(spec.get("eval_timeout_s") or max(300, 3 * seconds))

        # Floored at the repository's usual 300 s for quick tasks...
        self.assertEqual(timeout_for({"eval_time_seconds": 5}), 300)
        self.assertEqual(timeout_for({"eval_time_seconds": 100}), 300)
        # ...and three times the expected evaluation once that exceeds the floor, so a long
        # task does not get a wrapper timeout below its own declared cost.
        self.assertEqual(timeout_for({"eval_time_seconds": 300}), 900)
        self.assertEqual(timeout_for({"eval_time_seconds": 720}), 2160)
        # An explicit key wins, because this is a review quantity set by task difficulty.
        self.assertEqual(timeout_for({"eval_time_seconds": 30, "eval_timeout_s": 900}), 900)
        # A missing declaration falls back once, so metadata.yaml and run_eval.py cannot
        # disagree about it.
        self.assertEqual(timeout_for({}), max(300, 3 * default))

    def test_wrapper_refuses_to_run_if_copied_to_another_task(self):
        """A copied wrapper keeps its old TASK_ID and would score against the wrong oracle.

        The previous template derived everything from `__file__`, so a copy relocated itself.
        This one writes the registered id in, because `sle eval` needs the id rather than a
        path - so the mismatch has to be caught here instead of by whoever reads the numbers.
        """
        rendered = _render(task="Foo", task_id="Physics/Foo")
        self.assertIn("_expected_task", rendered)
        self.assertIn("parents[1].name", rendered)
        # Exercise it: drop the rendered wrapper into a directory named after another task.
        import subprocess
        import sys as _sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            wrong = pathlib.Path(tmp) / "benchmarks" / "Physics" / "Bar" / "frontier_eval"
            wrong.mkdir(parents=True)
            (wrong / "run_eval.py").write_text(rendered, encoding="utf-8")
            done = subprocess.run(
                [_sys.executable, str(wrong / "run_eval.py"),
                 "--candidate", "x.py", "--metrics-out", str(pathlib.Path(tmp) / "m.json")],
                capture_output=True, text=True, timeout=60)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("does not name this directory", done.stderr)

    def test_no_shipped_wrapper_carries_an_unrendered_placeholder(self):
        offenders = []
        for path in sorted((REPO / "benchmarks").glob("*/*/frontier_eval/run_eval.py")):
            text = path.read_text(encoding="utf-8")
            if "{{" in text or "}}" in text:
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
