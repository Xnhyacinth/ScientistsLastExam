"""Reproduce construction comparisons; writes no task or global audit files."""
from pathlib import Path
from itertools import combinations_with_replacement
import argparse
import importlib.util
import json
import numpy as np

HERE = Path(__file__).resolve().parent


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summary(metrics):
    return {key: value for key, value in metrics.items() if key != "per_world"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise-repeats", type=int, default=0)
    args = parser.parse_args()
    ev = load(HERE / "evaluator.py")
    ref = load(HERE / "reference_assignment.py")
    results = {}
    policies = {
        "reference": ref.assign_composition,
        "no_adaptation": lambda p, s: ref._round_mass(ref.sparse_design(p, s, adaptive=False), 500),
        "no_rounding": lambda p, s: ref.sparse_design(p, s),
        "model_average": lambda p, s: ref._round_mass(ref.sparse_design(p, s, model_average=True), 500),
        "dense_planning": lambda p, s: ref.infer(p, s),
        "dense_without_sparse_refit": lambda p, s: ref.infer(p, s, sparse_refit=False),
        "no_adequacy_check": lambda p, s: ref._round_mass(ref.sparse_design(p, s, adequacy_check=False), 500),
        "initial_only": lambda p, s: ref._round_mass(ref.sparse_design(p, s, plan=()), 500),
        "blanket_refusal": lambda p, s: dict(taxa=[], ambiguous_groups=[], abstain=True),
    }
    for name, policy in policies.items():
        results[name] = summary(ev.evaluate(policy))
        print(json.dumps({name: results[name]}), flush=True)
    fixed = []
    for plan in combinations_with_replacement(range(1, ev.N_PANELS), ev.BUDGET):
        metrics = ev.evaluate(lambda p, s: ref._round_mass(ref.sparse_design(p, s, plan=plan), 500))
        fixed.append(dict(plan=plan, **summary(metrics)))
    selected = max(fixed, key=lambda row: row["combined_score"])
    print(json.dumps(dict(fixed_plan_count=len(fixed), development_selected_fixed_plan=selected, all_fixed_plans=fixed)), flush=True)
    precision = []
    for bins in (50, 100, 200, 500, 1000):
        metrics = ev.evaluate(lambda p, s: ref._round_mass(ref.sparse_design(p, s), bins))
        precision.append(dict(bins=bins, **summary(metrics)))
    print(json.dumps(dict(development_precision_scan=precision)), flush=True)
    quantized = []
    for grid in (.01, .025, .05, .1, .2, "old_constants"):
        def rounded(p, s):
            output = ref.assign_composition(p, s)
            claims = output["taxa"] + output["ambiguous_groups"]
            for row in claims:
                row["abundance"] = (min((.35, .45, .55, .65), key=lambda x: abs(x-row["abundance"]))
                                    if grid == "old_constants" else max(0., round(row["abundance"]/grid)*grid))
            total = sum(row["abundance"] for row in claims)
            if total:
                for row in claims:
                    row["abundance"] /= total
            return output
        quantized.append(dict(grid=grid, **summary(ev.evaluate(rounded))))
    print(json.dumps(dict(quantization=quantized)), flush=True)
    # Retain legally acquired observations once. Evaluate cheap refusal rules
    # against the same fitted composition, without uncharged extra reads.
    features = []
    def cached(p, sequence):
        observations = [p["initial_observation"]]
        def record(panel):
            result = sequence(panel)
            observations.append(result)
            return result
        output = ref._round_mass(ref.sparse_design(p, record, adequacy_check=False), 500)
        matrix, indices = ref._blocks(p)
        max_fraction, entropy, envelope = [], [], []
        for observation in observations:
            selected = indices[observation["panel_id"]]
            frequency = np.asarray(observation["marker_counts"])[selected]/observation["read_count"]
            block = matrix[selected]
            columns = block/block.sum(axis=0)
            max_fraction.append(float(max(frequency)))
            entropy.append(float(-np.sum(frequency*np.log(np.maximum(frequency, 1e-16)))))
            envelope.append(float(max(np.max(frequency-columns.max(axis=1)), np.max(columns.min(axis=1)-frequency))))
        features.append([max_fraction[0], max(max_fraction), entropy[0], min(entropy), envelope[0], max(envelope)])
        return output
    cached_metrics = ev.evaluate(cached)
    features = np.asarray(features)
    rows = cached_metrics["per_world"]
    probes = []
    for feature in range(features.shape[1]):
        values = sorted(set(features[:12, feature]))
        thresholds = [values[0]-1] + [(a+b)/2 for a, b in zip(values, values[1:])] + [values[-1]+1]
        for threshold in thresholds:
            for direction in (-1, 1):
                scores = []
                for i, row in enumerate(rows):
                    refuse = direction*features[i, feature] > direction*threshold
                    scores.append(float(refuse) if row["kind"] == "out_of_library" else (0. if refuse else row["mechanism"]))
                probes.append(dict(feature=feature, threshold=threshold, direction=direction,
                                   development=max(0., (np.mean(scores[:12])-.25)/.75),
                                   heldout=max(0., (np.mean(scores[12:])-.25)/.75)))
    print(json.dumps(dict(scalar_rule_count=len(probes), development_selected_scalar_rule=max(probes, key=lambda row: row["development"]))), flush=True)
    repeats = []
    for repeat in range(1, args.noise_repeats+1):
        metrics = ev.evaluate(ref.assign_composition, noise_repeat=repeat)
        repeats.append(summary(metrics))
    if repeats:
        print(json.dumps(dict(noise_repeats=repeats)), flush=True)


if __name__ == "__main__":
    main()
