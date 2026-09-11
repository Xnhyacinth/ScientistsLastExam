"""Independent scientific and adversarial checks for marker mixture assignment."""
from copy import deepcopy
from itertools import combinations_with_replacement
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import numpy as np
import pytest
from _sandbox_tools import skip_unless_sandbox
from sle import frontier_eval_entrypoint
from sle.metric_visibility import SEARCH_VISIBLE_KEYS

TASK = Path(__file__).resolve().parents[1]/"benchmarks/Biology/MetagenomeCompositionAssignment"


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ev = load(TASK/"verification/evaluator.py")
ref = load(TASK/"verification/reference_assignment.py")
base = load(TASK/"solution.py")
wrapper = load(TASK/"frontier_eval/run_eval.py")


@pytest.fixture(scope="module")
def reference_metrics():
    return ev.evaluate(ref.assign_composition)


def test_balanced_larger_panel_and_continuous_truth():
    assert len(ev.SPECS) == 24
    sizes, values = set(), set()
    for indices in (ev.DEV, ev.HELD):
        kinds = [ev.SPECS[i][0] for i in indices]
        assert kinds.count("supported") == 6 and kinds.count("alias") == kinds.count("out_of_library") == 3
    for kind, seed in ev.SPECS:
        weights, probabilities = ev._truth(kind, seed)
        sizes.add(np.count_nonzero(weights)); values.update(weights[weights > 0])
        assert abs(weights.sum()-1) < 1e-12 and min(weights[weights > 0]) > .08
        assert np.all(probabilities > 0) and abs(probabilities.sum()-1) < 1e-12
    assert sizes == {3, 4} and len(values) > 50


def test_no_alias_list_or_zero_marker_and_library_distribution_is_category_blind():
    for _, seed in ev.SPECS:
        problems = [ev._problem(kind, seed) for kind in ("supported", "alias", "out_of_library")]
        for p in problems:
            assert "known_alias_groups" not in p
            assert np.all(np.asarray(p["reference_profiles"]) > 0)
        for key in ("reference_profiles", "available_panels", "panel_markers", "taxon_ids", "marker_ids"):
            assert problems[0][key] == problems[1][key] == problems[2][key]


def test_shared_marker_outside_worlds_stay_inside_every_coordinate_envelope():
    for kind, seed in ev.SPECS:
        if kind != "out_of_library":
            continue
        a, _ = ev._library(seed)
        _, q = ev._truth(kind, seed)
        # Outside even the linear span, despite being inside all marginal boxes.
        assert np.linalg.norm(a@np.linalg.lstsq(a, q, rcond=None)[0]-q) > 1e-4
        for panel in range(ev.N_PANELS):
            block = a[panel*6:(panel+1)*6]
            templates = block/block.sum(axis=0)
            observed = q[panel*6:(panel+1)*6]; observed = observed/observed.sum()
            assert np.all(observed >= templates.min(axis=1)-1e-12)
            assert np.all(observed <= templates.max(axis=1)+1e-12)


def test_diagnostic_panel_conserves_unmeasured_group_abundance():
    for _, seed in ev.SPECS:
        a, inverse = ev._library(seed)
        diagnostics = set()
        p = ev._problem("supported", seed)
        best = ev._best_separation(p)
        for pair in ((2, 3), (4, 5), (6, 7), (8, 9)):
            i, j = inverse[list(pair)]
            different = np.flatnonzero(np.abs(a[:, i]-a[:, j]) > 1e-12)
            assert len(different) == 6
            assert len(set(different//6)) == 1
            diagnostics.add(int(different[0]//6))
            remaining = np.setdiff1d(np.arange(ev.N_MARKERS), different)
            np.testing.assert_allclose(a[remaining, i], a[remaining, j], atol=1e-15)
            assert abs(a[different, i].sum()-a[different, j].sum()) < 1e-14
            assert best[i, j] >= 36-1e-8
        assert len(diagnostics) == 4 and 0 not in diagnostics
        assert best[inverse[0], inverse[1]] < p["resolution_threshold"]


def test_active_diagnostics_compete_for_budget_without_fixed_labels():
    active_sets = set()
    for kind, seed in ev.SPECS:
        _, inverse = ev._library(seed)
        weights, _ = ev._truth(kind, seed)
        active = tuple(i for i in (2, 4, 6, 8) if weights[inverse[[i, i+1]]].sum() > 0)
        assert len(active) == ev.BUDGET == 2
        active_sets.add(active)
    assert len(active_sets) == 6


def test_counts_charge_and_stream_binding():
    kind, seed = ev.SPECS[0]
    one, two = ev._Sequencer(kind, seed), ev._Sequencer(kind, seed)
    first = one(1); one(2); two(2)
    assert first == two(1)
    assert sum(first["marker_counts"]) == first["read_count"] == ev.READS
    assert np.count_nonzero(first["marker_counts"]) == 6
    repeat = ev._Sequencer(kind, seed)
    assert repeat(1) != repeat(1)
    with pytest.raises(RuntimeError):
        repeat(1)
    assert repeat.violated


@pytest.mark.parametrize("args", [(1.0,), (True,), (), (1, 2), ("1",), (0,), (ev.N_PANELS,)])
def test_malformed_requests_permanently_invalidate_even_if_caught(args):
    lab = ev._Sequencer(*ev.SPECS[0])
    with pytest.raises((TypeError, ValueError, RuntimeError)):
        lab(*args)
    assert lab.violated and lab.calls == 0
    with pytest.raises(RuntimeError):
        lab(1)


def test_budget_violation_cannot_be_hidden_by_returning_a_valid_shape():
    def overrun(p, s):
        for _ in range(3):
            try: s(1)
            except RuntimeError: pass
        return dict(taxa=[], ambiguous_groups=[], abstain=True)
    m = ev.evaluate(overrun)
    assert m["valid"] == m["combined_score"] == m["heldout_scientific_score"] == 0


def test_strict_schema_and_nonoverlapping_abundance_mass():
    p = ev._problem(*ev.SPECS[0])
    for abundance in (True, "0.4", float("nan"), float("inf"), -.1):
        assert ev._parse(dict(taxa=[dict(taxon="t0", abundance=abundance)], ambiguous_groups=[], abstain=False), p) is None
    assert ev._parse(dict(taxa=[], ambiguous_groups=[["t0", "t1"]], abstain=False), p) is None
    assert ev._parse(dict(taxa=[dict(taxon="t0", abundance=.5)], ambiguous_groups=[dict(taxa=["t0", "t1"], abundance=.5)], abstain=False), p) is None
    assert ev._parse(dict(taxa=[dict(taxon="t0", abundance=.8), dict(taxon="t1", abundance=.8)], ambiguous_groups=[], abstain=False), p) is None


def test_scoring_inputs_are_not_candidate_mutable(reference_metrics):
    def mutate(p, s):
        out = ref.assign_composition(p, s)
        p["abundance_tolerance"] = 1e99
        p["resolution_threshold"] = 1e99
        p["taxon_ids"].clear()
        return out
    assert ev.evaluate(mutate) == reference_metrics


def test_baseline_refusal_and_one_invalid_world(reference_metrics):
    assert reference_metrics["valid"] == 1
    assert 0 < reference_metrics["combined_score"] <= 1
    for policy in (base.assign_composition, lambda p, s: dict(taxa=[], ambiguous_groups=[], abstain=True)):
        m = ev.evaluate(policy)
        assert m["valid"] == 1 and m["combined_score"] == m["heldout_scientific_score"] == 0
    calls = 0
    def invalid_once(p, s):
        nonlocal calls
        calls += 1
        return None if calls == 15 else ref.assign_composition(p, s)
    m = ev.evaluate(invalid_once)
    assert m["valid"] == m["combined_score"] == m["heldout_scientific_score"] == 0
    assert sum(row["valid"] for row in m["per_world"]) == 23


def test_axes_count_every_claim_and_keep_alias_and_refusal_denominators(reference_metrics):
    for prefix, indices in (("development", ev.DEV), ("heldout", ev.HELD)):
        rows = [reference_metrics["per_world"][i] for i in indices]
        assert reference_metrics[prefix+"_claim_count"] == sum(r["claimed"] for r in rows)
        assert reference_metrics[prefix+"_false_discovery_count"] == sum(r["false"] for r in rows)
        assert reference_metrics[prefix+"_alias_group_count"] == 3
        assert reference_metrics[prefix+"_refusal_world_count"] == 3
        assert reference_metrics[prefix+"_correct_refusal_rate"] == 1
        assert reference_metrics[prefix+"_alias_resolution_rate"] == 1


def test_pair_separation_and_group_algorithms_agree_independently():
    for _, seed in ev.SPECS[:4]:
        p = ev._problem("supported", seed)
        a, indices = ref._blocks(p)
        for plan in ((), (1,), (1, 1), (2, 4)):
            observations = [p["initial_observation"]] + [ev._observation("supported", seed, panel, i) for i, panel in enumerate(plan)]
            counts = {0: 1}
            for panel in plan: counts[panel] = counts.get(panel, 0)+1
            actual = {frozenset(x) for x in ev._components(p, ev._separation(p, counts))}
            expected = {frozenset(x) for x in ref._groups(p, a, indices, observations)}
            assert actual == expected


def test_reference_follows_renamed_taxa_and_marker_rows():
    p = ev._problem("alias", 3107)
    original = ref.assign_composition(p, ev._Sequencer("alias", 3107))
    p = deepcopy(p)
    names = {name: "renamed_"+name for name in p["taxon_ids"]}
    p["taxon_ids"] = [names[name] for name in p["taxon_ids"]]
    result = ref.assign_composition(p, ev._Sequencer("alias", 3107))
    for row in original["taxa"]: row["taxon"] = names[row["taxon"]]
    for row in original["ambiguous_groups"]: row["taxa"] = [names[name] for name in row["taxa"]]
    assert original == result


def test_conditional_likelihood_matches_closed_form_two_taxon_solution():
    a = np.array([[.45, .03], [.30, .12], [.20, .70], [.05, .15]])
    truth = np.array([.27, .73])
    indices = {0: [0, 1], 1: [2, 3]}
    observations = []
    for panel, chosen in indices.items():
        probabilities = a[chosen] @ truth
        probabilities /= probabilities.sum()
        counts = np.zeros(4); counts[chosen] = probabilities*300000
        observations.append(dict(panel_id=panel, marker_counts=counts.tolist(), read_count=300000))
        # Solve a single conditional odds equation analytically, independently
        # of the optimizer or its derivative implementation.
        f = probabilities[0]
        first = a[chosen[0]]; totals = a[chosen].sum(axis=0)
        solved = (first[1]-f*totals[1])/(f*(totals[0]-totals[1])-(first[0]-first[1]))
        assert abs(solved-truth[0]) < 1e-12
    fitted, deviance = ref._fit(a, indices, observations)
    np.testing.assert_allclose(fitted, truth, atol=1e-6)
    assert abs(deviance) < 1e-6


def test_reference_and_resolution_are_invariant_to_marker_row_permutation():
    p = ev._problem("alias", 3107)
    original = ref.assign_composition(p, ev._Sequencer("alias", 3107))
    order = np.random.default_rng(34).permutation(ev.N_MARKERS)
    shuffled = deepcopy(p)
    for key in ("marker_ids", "reference_profiles"):
        shuffled[key] = [p[key][i] for i in order]
    shuffled["initial_observation"]["marker_counts"] = [p["initial_observation"]["marker_counts"][i] for i in order]
    lab = ev._Sequencer("alias", 3107)
    def sequence(panel):
        row = lab(panel)
        row["marker_counts"] = [row["marker_counts"][i] for i in order]
        return row
    assert original == ref.assign_composition(shuffled, sequence)
    np.testing.assert_array_equal(ev._separation(p, {0: 1, 1: 1}), ev._separation(shuffled, {0: 1, 1: 1}))


def test_perfect_truth_has_a_legal_full_credit_design():
    worlds = iter(ev.SPECS)
    def ideal(p, sequence):
        kind, seed = next(worlds)
        if kind == "out_of_library":
            return dict(taxa=[], ambiguous_groups=[], abstain=True)
        weights, _ = ev._truth(kind, seed)
        best = ev._best_separation(p)
        options = []
        for plan in combinations_with_replacement(p["available_panels"], p["panel_budget"]):
            counts = {0: 1}
            for panel in plan: counts[panel] = counts.get(panel, 0)+1
            groups = ev._components(p, ev._separation(p, counts))
            reward = sum(sum(weights[i] for i in group)*(1 if len(group) == 1 or all(best[i,j] < p["resolution_threshold"] for i in group for j in group) else .5) for group in groups)
            options.append((reward, plan, groups))
        reward, plan, groups = max(options, key=lambda item: item[0])
        assert abs(reward-1) < 1e-12
        for panel in plan: sequence(panel)
        out = dict(taxa=[], ambiguous_groups=[], abstain=False)
        for group in groups:
            mass = float(sum(weights[i] for i in group))
            if not mass: continue
            names = [p["taxon_ids"][i] for i in sorted(group)]
            if len(names) == 1: out["taxa"].append(dict(taxon=names[0], abundance=mass))
            else: out["ambiguous_groups"].append(dict(taxa=names, abundance=mass))
        return out
    metrics = ev.evaluate(ideal)
    assert metrics["valid"] == 1
    assert abs(metrics["combined_score"]-1) < 1e-12
    assert abs(metrics["heldout_scientific_score"]-1) < 1e-12


@pytest.mark.parametrize("output", [
    None, [], {},
    dict(taxa=[], ambiguous_groups=[], abstain=1),
    dict(taxa=[], ambiguous_groups=[], abstain=False, extra=True),
    dict(taxa="t0", ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="unknown", abundance=.5)], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=True)], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance="0.5")], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=float("nan"))], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=float("inf"))], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=-.1)], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=1.1)], ambiguous_groups=[], abstain=False),
    dict(taxa=[dict(taxon="t0", abundance=.5)], ambiguous_groups=[], abstain=True),
    dict(taxa=[], ambiguous_groups=[dict(taxa=["t0"], abundance=.5)], abstain=False),
    dict(taxa=[], ambiguous_groups=[dict(taxa=["t0", "t0"], abundance=.5)], abstain=False),
])
def test_malformed_outputs_zero_all_aggregate_scores(output):
    m = ev.evaluate(lambda p, s: deepcopy(output))
    assert m["valid"] == m["combined_score"] == m["heldout_scientific_score"] == 0


def test_reference_reproducibility_and_actual_two_call_budget(reference_metrics):
    assert ev.evaluate(ref.assign_composition) == reference_metrics
    lab = ev._Sequencer(*ev.SPECS[0])
    ref.assign_composition(ev._problem(*ev.SPECS[0]), lab)
    assert lab.calls == 2 and not lab.violated


def test_initial_screen_confounds_groups_but_followups_separate_them():
    for _, seed in ev.SPECS:
        a, inverse = ev._library(seed)
        for first, second in ((2, 4), (6, 8)):
            i, j = inverse[[first, second]]
            np.testing.assert_allclose(a[:6, i]/a[:6, i].sum(),
                                       a[:6, j]/a[:6, j].sum(), atol=1e-14)
            distances = []
            for panel in range(1, ev.N_PANELS):
                block = a[panel*6:(panel+1)*6, :][:, [i, j]]
                roots = np.sqrt(block/block.sum(axis=0))
                distances.append(ev.READS*ev.MINIMUM_ABUNDANCE*np.sum((roots[:, 0]-roots[:, 1])**2))
            assert max(distances) >= ev.RESOLUTION_THRESHOLD


@skip_unless_sandbox("bwrap")
def test_task_local_wrapper_runs_real_sandbox_and_seals_heldout_metrics(tmp_path):
    metrics_path = tmp_path/"metrics.json"
    completed = subprocess.run(
        [sys.executable, str(TASK/"frontier_eval/run_eval.py"),
         "--candidate", str(TASK/"solution.py"),
         "--metrics-out", str(metrics_path)],
        capture_output=True, text=True, timeout=180,
    )
    assert completed.returncode == 0, completed.stderr
    public = json.loads(metrics_path.read_text())
    assert json.loads(completed.stdout) == public
    assert set(public) <= set(SEARCH_VISIBLE_KEYS)
    assert public["combined_score"] == public["raw_score"] == 0
    assert public["valid"] == 1
    assert not any(key.startswith("heldout_") for key in public)
    assert "per_world" not in public


def test_task_local_wrapper_uses_shared_trusted_entrypoint():
    source = (TASK/"frontier_eval/run_eval.py").read_text()
    assert "sle/frontier_eval_entrypoint.py" in source
    assert 'import evaluator' not in source and 'CandidateProxy' not in source


def test_task_local_wrapper_strips_credentials(monkeypatch):
    monkeypatch.setenv("DEMO_API_KEY", "secret")
    monkeypatch.setenv("AUTHORIZATION", "secret")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret")
    monkeypatch.setenv("SLE_TRUSTED_EVAL_LOG", "/trusted/operator.log")
    monkeypatch.setenv("SAFE_SETTING", "kept")
    environment = frontier_eval_entrypoint.child_environment(wrapper.ROOT)
    assert "DEMO_API_KEY" not in environment
    assert "AUTHORIZATION" not in environment
    assert "DATABASE_PASSWORD" not in environment
    assert "SLE_TRUSTED_EVAL_LOG" not in environment
    assert environment["SAFE_SETTING"] == "kept"
    assert environment["PYTHONPATH"] == str(wrapper.ROOT)


def test_task_local_wrapper_treats_child_failure_as_infrastructure(
        tmp_path, monkeypatch, capsys):
    output = tmp_path/"public"/"metrics.json"
    output.parent.mkdir()
    trusted = tmp_path/"private"
    output.write_text('{"combined_score": 1}')

    class Failed:
        returncode = 17
        stdout = ""
        stderr = "/hidden/evaluator.py:9 secret-source-line"

    monkeypatch.setattr(frontier_eval_entrypoint.subprocess, "run", lambda *args, **kwargs: Failed())
    result = frontier_eval_entrypoint.run(wrapper.TASK_ID, wrapper.ROOT, wrapper.EVAL_TIMEOUT_S, [
        "--candidate", str(TASK/"solution.py"),
        "--metrics-out", str(output),
        "--full-metrics-dir", str(trusted),
    ])
    captured = capsys.readouterr()
    assert result == 2 and not output.exists()
    assert "secret-source-line" not in captured.err
    diagnostic = json.loads((trusted/"last_infrastructure_failure.json").read_text())
    assert diagnostic["stage"] == "launching trusted evaluation"
    assert diagnostic["returncode"] == 17
    assert diagnostic["stderr"].endswith("secret-source-line")
