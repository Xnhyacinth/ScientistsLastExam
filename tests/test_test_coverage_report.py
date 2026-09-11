from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.summarize_test_coverage import markdown, summarize


class TestCoverageReportTests(unittest.TestCase):
    def _report(self, cases, required=None):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "junit.xml"
            path.write_text("<testsuites><testsuite>" + cases + "</testsuite></testsuites>")
            return summarize(path, required)

    def test_skipped_evidence_is_visible_without_claiming_execution(self):
        report = self._report(
            '<testcase classname="C" name="portable"/>'
            '<testcase classname="C" name="recorded"><skipped message="raw runs unavailable"/></testcase>'
        )
        self.assertTrue(report["passed"])
        self.assertFalse(report["coverage_complete"])
        self.assertEqual(report["executed_count"], 1)
        self.assertEqual(report["collected_count"], 2)
        self.assertIn("raw runs unavailable", markdown(report))

    def test_required_replay_cannot_pass_when_skipped_or_not_collected(self):
        for cases in (
            '<testcase classname="C" name="portable"/>',
            '<testcase classname="C" name="recorded"><skipped message="missing"/></testcase>',
        ):
            report = self._report(cases, ["C::recorded"])
            self.assertFalse(report["passed"])
            self.assertFalse(report["coverage_complete"])
            self.assertNotEqual(report["required_tests"][0]["status"], "passed")

    def test_failed_error_empty_and_duplicate_reports_fail(self):
        for cases in (
            "",
            '<testcase classname="C" name="x"><failure message="changed hash"/></testcase>',
            '<testcase classname="C" name="x"><error message="collection failed"/></testcase>',
            '<testcase classname="C" name="x"/><testcase classname="C" name="x"/>',
        ):
            self.assertFalse(self._report(cases)["passed"])

    def test_complete_required_replay_is_order_independent(self):
        cases = ['<testcase classname="C" name="one"/>', '<testcase classname="C" name="two"/>']
        first = self._report("".join(cases), ["C::one", "C::two"])
        second = self._report("".join(reversed(cases)), ["C::two", "C::one"])
        self.assertTrue(first["passed"])
        self.assertTrue(first["coverage_complete"])
        self.assertEqual(first["counts"], second["counts"])
        self.assertEqual(first["required_tests"], second["required_tests"])
