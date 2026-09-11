"""Discovery-contract pins for SparseVectorAudit.

The public score is mechanism, normalised so that declining every world is exactly zero and so is
claiming a violation everywhere. A world where the claim holds is the unsupported case: declining
it is correct, declining everything is not; a world where the claim fails is determinable and a
witness is the answer.

Five of these tests pin what the construction found the hard way: that the specification is
compliant and tight, that the compliant deviations live below delta, that every violating world
has a witness above epsilon, that the confirmation is what separates an audit from a guess, and
that a false witness costs a world even where the claim fails.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TASK = ROOT / "benchmarks/ComputerScience/SparseVectorAudit"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _straddle(ev, mech):
    """The pair that straddles a branch's offset at its first position, everything else at the
    bottom of the range, and the event that the query at that position dissents."""
    offset, side, positions = mech.branch
    i = positions[0]
    dataset, neighbour = [ev.QUERY_MIN] * mech.k, [ev.QUERY_MIN] * mech.k
    if side == "up":
        dataset[i], neighbour[i] = ev.THRESHOLD + offset, ev.THRESHOLD + offset - 1
        event = [p for p in mech.patterns if p[i:i + 1] == "F"]
    else:
        dataset[i], neighbour[i] = ev.THRESHOLD - offset, ev.THRESHOLD - offset + 1
        event = [p for p in mech.patterns if p[i:i + 1] == "T"]
    return dataset, neighbour, event


class SparseVectorAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "sparse_vector_oracle")
        cls.baseline = _load(TASK / "solution.py", "sparse_vector_baseline")
        cls.reference = _load(TASK / "verification/reference_library_scan.py", "sparse_vector_reference")
        cls.specs = cls.evaluator.DEVELOPMENT_WORLDS + cls.evaluator.HELDOUT_WORLDS
        cls.full = cls.evaluator.evaluate(cls.reference.audit)

    def _variant(self, old, new):
        source = (TASK / "verification/reference_library_scan.py").read_text(encoding="utf-8")
        self.assertEqual(source.count(old), 1, old)
        namespace = {}
        exec(compile(source.replace(old, new), "reference_variant", "exec"), namespace)  # noqa: S102
        return namespace["audit"]

    def test_blanket_refusal_in_both_forms_and_a_blind_claim_score_zero(self):
        for submission in ({"verdict": "no_violation", "confidence": 1.0}, {"abstain": True}):
            metrics = self.evaluator.evaluate(lambda _p, _s, s=submission: dict(s))
            self.assertEqual(metrics["valid"], 1.0, submission)
            self.assertEqual(metrics["combined_score"], 0.0, submission)
            self.assertEqual(metrics["development_correct_refusal_rate"], 1.0, submission)
            self.assertEqual(metrics["development_raw_mechanism"], 5.0 / 12.0, submission)

        def blind(problem, _s):
            # a straddle at offset 12 above the threshold, the first query: right in one world
            k, t = problem["n_queries"], problem["threshold"]
            return {"verdict": "violation", "dataset": [t + 12] + [0] * (k - 1),
                    "neighbour": [t + 11] + [0] * (k - 1),
                    "event": [o for o in problem["output_patterns"] if o[:1] == "F"], "confidence": 0.9}
        metrics = self.evaluator.evaluate(blind)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["combined_score"], 0.0)
        self.assertGreater(metrics["development_false_discovery_rate"], 0.8)

    def test_the_specification_is_compliant_and_tight(self):
        """Implemented as specified the mechanism is epsilon-DP (Lyu, Su and Li 2017, Alg. 1), so
        no exact witness exceeds epsilon; with one output T four fixed pairs already reach 0.8."""
        ev = self.evaluator
        for spec in self.specs:
            if spec["kind"] != "compliant":
                continue
            mech = ev._Mechanism(spec)
            t, k = ev.THRESHOLD, mech.k
            pairs = [([t + 1] + [t - 1] * (k - 1), [t] + [t] * (k - 1)),
                     ([t - 1] * k, [t] * k), ([t] * k, [t + 1] * k),
                     ([t - 1] * 5 + [t + 1] * (k - 5), [t] * 5 + [t] * (k - 5))]
            best = max(max(ev.best_event_loss(mech, a, b)[0], ev.best_event_loss(mech, b, a)[0])
                       for a, b in pairs)
            self.assertLessEqual(best, ev.EPSILON, spec["name"])
            if mech.c == 1:
                self.assertGreater(best, 0.8, spec["name"])

    def test_the_compliant_deviations_live_below_delta(self):
        """A compliant-branch deployment skips the noise far from the threshold. Coupled with the
        specification it differs only when a correct comparison would have dissented, which
        bounds delta by eta (1 + e^epsilon) below the claimed 0.001; the straddling event that
        breaks every branch world is rarer than delta here, so its loss is minus infinity."""
        ev = self.evaluator
        count = 0
        for spec in self.specs:
            if spec["kind"] != "compliant_branch":
                continue
            count += 1
            mech = ev._Mechanism(spec)
            offset, side, positions = mech.branch
            if side == "up":
                flip = float(np.sum(mech.rho_p * (1.0 - ev._tail_ge(mech.b_nu, mech.rho - offset))))
            else:
                flip = float(np.sum(mech.rho_p * ev._tail_ge(mech.b_nu, mech.rho + offset)))
            eta = flip if (side == "up" and mech.c == 1) else flip * len(positions)
            self.assertLess(eta * (1.0 + math.exp(ev.EPSILON)), ev.DELTA, spec["name"])
            loss, p1, p2 = ev.witness_loss(mech, *_straddle(ev, mech))
            self.assertEqual(loss, -math.inf, spec["name"])
            self.assertLess(max(p1, p2), ev.DELTA, spec["name"])
        self.assertEqual(count, 3)

    def test_every_violating_world_has_a_witness_above_epsilon(self):
        ev = self.evaluator
        for spec in self.specs:
            if spec["kind"] not in ("noise_scale", "branch"):
                continue
            world = ev._world(spec)
            self.assertGreater(world["anchor_loss"], ev.EPSILON + 0.2, spec["name"])
            if spec["kind"] == "branch":
                mech = world["mechanism"]
                loss, p1, p2 = ev.witness_loss(mech, *_straddle(ev, mech))
                self.assertEqual(loss, math.inf, spec["name"])
                self.assertGreater(max(p1, p2), 0.01, spec["name"])
            else:
                self.assertLess(world["anchor_loss"], 1.6, spec["name"])

    def test_the_reference_and_the_baseline(self):
        ev, full = self.evaluator, self.full
        baseline = ev.evaluate(self.baseline.audit)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertEqual(baseline["development_false_discovery_rate"], 1.0)
        self.assertEqual(full["valid"], 1.0)
        self.assertGreater(full["combined_score"], 0.45)
        self.assertLess(full["combined_score"], 0.8)
        self.assertEqual(full["development_false_discovery_rate"], 0.0)
        self.assertEqual(full["heldout_false_discovery_rate"], 0.0)
        self.assertEqual(full["development_correct_refusal_rate"], 1.0)
        # The reference leaves violations unnamed on purpose; if it names every one the task has
        # stopped measuring the axis it was built around.
        self.assertLess(full["development_discovery_coverage"], 1.0)
        self.assertLess(full["heldout_discovery_coverage"], 1.0)
        for row in full["per_instance"]:
            self.assertLessEqual(row["samples_used"], ev.SAMPLE_BUDGET, row)
            if row["kind"] in ev.REFUSAL_KINDS:
                self.assertTrue(row["abstained"], row)

    def test_confirmation_is_what_separates_an_audit_from_a_guess(self):
        """Claiming the best screened pair without confirming it on fresh runs makes false
        discoveries; each one costs a world, including where the claim does fail."""
        no_confirm = self._variant(
            "    # --- confirm on fresh samples",
            "    if pairs[0][0] > eps:\n        _v, first, second, event = pairs[0]\n"
            "        return {\"verdict\": \"violation\", \"dataset\": list(first), \"neighbour\": list(second),\n"
            "                \"event\": event, \"confidence\": 0.8}\n"
            "    return {\"verdict\": \"no_violation\", \"confidence\": 0.7}\n"
            "    # --- confirm on fresh samples")
        metrics = self.evaluator.evaluate(no_confirm)
        self.assertGreater(metrics["development_false_discovery_rate"], 0.0)
        self.assertLess(metrics["combined_score"], self.full["combined_score"] - 0.1)
        self.assertLess(metrics["heldout_mechanism_score"], self.full["heldout_mechanism_score"] - 0.2)

    def test_the_scan_and_the_library_both_earn(self):
        no_scan = self._variant('    for side in ("up", "down"):\n        room', '    for side in ():\n        room')
        no_library = self._variant(
            "    # --- screen the library",
            '    return {"verdict": "no_violation", "confidence": 0.7}\n    # --- screen the library')
        full = self.full["combined_score"]
        self.assertLess(self.evaluator.evaluate(no_scan)["combined_score"], full - 0.3)
        self.assertLess(self.evaluator.evaluate(no_library)["combined_score"], full - 0.2)

    def test_a_false_witness_costs_a_world_where_the_claim_fails(self):
        ev = self.evaluator
        spec = next(s for s in ev.DEVELOPMENT_WORLDS if s["kind"] == "noise_scale")
        world = ev._world(spec)
        k, t = world["mechanism"].k, ev.THRESHOLD
        weak = (np.array([t] * k), np.array([t + 1] * k), ["T"])
        metrics = ev._metrics(world, weak)
        self.assertTrue(metrics["false_discovery"])
        self.assertEqual(metrics["mechanism_score"], -1.0)
        self.assertEqual(ev._metrics(world, None)["mechanism_score"], 0.0)

    def test_two_evaluations_are_identical(self):
        second = self.evaluator.evaluate(self.reference.audit)
        self.assertEqual(json.dumps(self.full, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_malformed_candidates_score_zero_without_raising(self):
        def raises(_p, _s):
            raise RuntimeError("boom")

        def overspend(problem, sample):
            k = problem["n_queries"]
            sample([50] * k, problem["sample_budget"])
            sample([50] * k, 1)
            return {"verdict": "no_violation"}

        def overspend_caught(problem, sample):
            try:
                overspend(problem, sample)
            except RuntimeError:
                pass
            return {"verdict": "no_violation"}

        def patched_budget(problem, sample):
            sample.budget = 10 ** 9  # a function attribute: the ledger is not reachable
            return overspend(problem, sample)

        def claim(**override):
            def audit(problem, _s):
                k = problem["n_queries"]
                out = {"verdict": "violation", "dataset": [50] * k, "neighbour": [51] * k,
                       "event": [problem["output_patterns"][0]], "confidence": 0.5}
                out.update({key: (value(k) if callable(value) else value) for key, value in override.items()})
                return out
            return audit

        shapes = {
            "raises": raises,
            "none": lambda _p, _s: None,
            "empty": lambda _p, _s: {},
            "string": lambda _p, _s: "violation",
            "verdict_bad": lambda _p, _s: {"verdict": "maybe"},
            "no_event": claim(event=None),
            "event_empty": claim(event=[]),
            "event_string": claim(event="T"),
            "event_unknown": claim(event=["TTTTTTTTTTTTTTTTTTTT"]),
            "event_repeat": claim(event=["T", "T"]),
            "dataset_short": claim(dataset=lambda k: [50] * (k - 1)),
            "dataset_float": claim(dataset=lambda k: [50.0] * k),
            "dataset_bool": claim(dataset=lambda k: [True] * k),
            "dataset_range": claim(dataset=lambda k: [101] * k, neighbour=lambda k: [100] * k),
            "not_neighbours": claim(neighbour=lambda k: [52] * k),
            "identical": claim(neighbour=lambda k: [50] * k),
            "confidence_nan": claim(confidence=float("nan")),
            "confidence_str": claim(confidence="high"),
            "overspend": overspend,
            "overspend_caught": overspend_caught,
            "patched_budget": patched_budget,
            "n_float": lambda p, s: s([50] * p["n_queries"], 10.0),
            "n_bool": lambda p, s: s([50] * p["n_queries"], True),
            "n_zero": lambda p, s: s([50] * p["n_queries"], 0),
            "n_too_big": lambda p, s: s([50] * p["n_queries"], self.evaluator.MAX_SAMPLES_PER_CALL + 1),
            "queries_short": lambda p, s: s([50], 10),
            "queries_float": lambda p, s: s([50.5] * p["n_queries"], 10),
        }
        self.assertGreaterEqual(len(shapes), 12)
        for name, candidate in shapes.items():
            metrics = self.evaluator.evaluate(candidate)
            self.assertEqual(metrics["valid"], 0.0, name)
            self.assertEqual(metrics["combined_score"], 0.0, name)
            self.assertEqual(metrics["feasibility_rate"], 0.0, name)

    def test_runs_are_charged_and_the_budget_fails_closed(self):
        ev = self.evaluator
        world = ev._world(self.specs[0])
        k = world["mechanism"].k
        campaign = ev._Campaign(world)
        sample = campaign.oracle()
        first = sample([50] * k, 1000)
        again = sample([50] * k, 1000)
        self.assertEqual(sum(first.values()), 1000)
        self.assertNotEqual(first, again)          # the same vector twice gives fresh runs
        self.assertEqual(campaign.spent, 2000)
        sample([49] * k, world["budget"] - 2000)
        with self.assertRaises(RuntimeError):
            sample([50] * k, 1)
        self.assertTrue(campaign.violated)
        # counts do not depend on the order in which different vectors are run
        a, b = ev._Campaign(world).oracle(), ev._Campaign(world).oracle()
        x1 = a([50] * k, 500); y1 = a([51] * k, 500)
        y2 = b([51] * k, 500); x2 = b([50] * k, 500)
        self.assertEqual((x1, y1), (x2, y2))

    def test_hidden_axes_stay_out_of_the_search_view(self):
        from sle.metric_visibility import SEARCH_VISIBLE_KEYS

        for key in SEARCH_VISIBLE_KEYS:
            self.assertNotIn("heldout", key)
            self.assertNotIn("mechanism", key)
            self.assertNotIn("witness", key)




class SparseVectorAdmissionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev = _load(TASK / "verification/evaluator.py", "sva_admission_oracle")
        cls.proof = _load(TASK / "verification/reference_compliance.py", "sva_independent_compliance")

    def test_infinite_geometric_tail_and_uniform_branch_bound(self):
        ev, proof = self.ev, self.proof
        for scale in (1.0, 2.0, 4.0, 8.0, 12.0):
            points = np.arange(-80, 81)
            expected = np.array([proof.dlap_tail(scale, int(x)) for x in points])
            np.testing.assert_allclose(ev._tail_ge(scale, points), expected, rtol=0, atol=2e-14)
        for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
            mechanism = ev._Mechanism(spec)
            self.assertLess(proof.distribution_truncation_bound(mechanism.b_rho, mechanism.b_nu, mechanism.k), 1e-40)
            if spec['kind'] == 'compliant_branch':
                offset, side, positions = mechanism.branch
                bound = proof.coupling_delta_bound(mechanism.b_rho, mechanism.b_nu, offset, side, len(positions), mechanism.c)
                self.assertLess(bound, ev.DELTA / 2, spec['name'])

    def test_every_output_distribution_is_normalized(self):
        for spec in self.ev.DEVELOPMENT_WORLDS + self.ev.HELDOUT_WORLDS:
            mechanism = self.ev._Mechanism(spec)
            for vector in ([0]*mechanism.k, [50]*mechanism.k, [100]*mechanism.k):
                distribution = mechanism.distribution(vector)
                self.assertTrue(np.all(distribution >= 0))
                self.assertAlmostEqual(float(distribution.sum()), 1.0, places=13)

    def test_fdr_counts_claims_and_zero_denominator_is_unavailable(self):
        import yaml
        from scripts.report_discovery_triple import extract
        rows=[]
        for kind,claimed,false in [('noise_scale',True,True),('branch',True,False),('compliant',False,False),('compliant',False,False)]:
            rows.append({'kind':kind,'valid':True,'abstained':not claimed,'false_discovery':false,
                         'mechanism_score':0.0,'witness_strength':0.0,'correct_refusal':not claimed,
                         'confidence_calibration_score':0.0,'samples_used':0})
        result=self.ev._split_summary(rows)
        self.assertEqual(result['false_discovery_count'],1)
        self.assertEqual(result['false_discovery_denominator'],2)
        self.assertEqual(result['false_discovery_rate'],0.5)
        self.assertEqual(result['all_world_false_claim_fraction'],0.25)
        refusal=self.ev.evaluate(lambda p,s:{'abstain':True})
        contract=yaml.safe_load((TASK/'TASK_CARD.yaml').read_text())['metric_contract']
        axis=extract(refusal,'heldout',contract)['fdr']
        self.assertEqual(axis['status'],'zero_denominator')
        self.assertIsNone(axis['value'])

    def test_partial_validity_does_not_make_the_task_valid(self):
        # A public-input condition invalidates only the k=11 held-out world.
        def candidate(problem,sample):
            return None if problem['n_queries']==11 else {'abstain':True}
        result=self.ev.evaluate(candidate)
        self.assertEqual(result['development_valid_count'],12)
        self.assertEqual(result['heldout_valid_count'],5)
        self.assertEqual(result['valid'],0.0)
        self.assertEqual(result['combined_score'],0.0)

    def test_positional_adaptation_keeps_original_helpers_and_body(self):
        legacy=(TASK/'verification/reference_library_scan.py').read_text()
        positional=(ROOT/'.research/sparse_vector_audit/headroom_positional.py').read_text()
        standalone=(TASK/'verification/reference_positional.py').read_text()
        helpers=legacy[legacy.index('import math'):legacy.index('def audit(problem, sample):')]
        body=positional[positional.index('LATER_STEP ='):].replace('ref.','')
        self.assertIn(helpers,standalone)
        self.assertTrue(standalone.endswith(body))
        self.assertNotIn('importlib',standalone.split('from __future__')[1])




class SparseVectorSandboxIsolationTests(unittest.TestCase):
    def test_real_candidate_proxy_resets_every_world_and_preserves_in_world_state(self):
        # Use the repository's platform guard: Linux with a broken sandbox fails loudly.
        if sys.platform != 'linux':
            self.skipTest('real CandidateProxy world isolation requires Linux')
        import tempfile
        import textwrap
        from unittest.mock import patch
        from sle.secure_eval import CandidateProxy
        ev = _load(TASK/'verification/evaluator.py', 'sva_session_oracle')
        source = '''
import os
counter = 0
def audit(problem, sample):
    global counter
    counter += 1
    previous = getattr(os, '_sva_world', 0)
    marker = '/tmp/sva_world_marker'
    stale = counter != 1 or previous != 0 or os.path.exists(marker)
    os._sva_world = previous + 1
    with open(marker, 'w') as handle:
        handle.write('same-world')
    for _ in range(2):
        counts = sample([50] * problem['n_queries'], 1)
        if sum(counts.values()) != 1 or counter != 1 or os._sva_world != 1:
            return None
        with open(marker) as handle:
            if handle.read() != 'same-world':
                return None
    return None if stale else {'abstain': True}
'''
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)/'candidate.py'
            candidate.write_text(textwrap.dedent(source))
            with CandidateProxy(candidate, 'audit', timeout_s=60) as proxy:
                with patch.object(proxy, 'reset_session', wraps=proxy.reset_session) as reset:
                    metrics = ev.evaluate(proxy)
                    self.assertEqual(reset.call_count, 18)
        self.assertEqual(metrics['valid'], 1.0)
        self.assertEqual(metrics['development_valid_count'], 12)
        self.assertEqual(metrics['heldout_valid_count'], 6)
        self.assertTrue(all(row['samples_used']==2 and row['valid'] for row in metrics['per_instance']))


if __name__ == "__main__":
    unittest.main()
