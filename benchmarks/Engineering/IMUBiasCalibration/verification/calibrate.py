"""Development-only shortcut selection, then independent Linux sandbox replay."""
from __future__ import annotations
import argparse
import importlib.util
import inspect
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "Sensors/IMUBiasCalibration"


def shortcut_fit(problem, rows):
    g, scale = problem["gravity_mps2"], problem["temperature_scale_c"]
    u = np.asarray([r["orientation"] for r in rows])
    x = np.asarray([(r["temperature_c"]-problem["reference_temperature_c"])/scale for r in rows])
    y = np.asarray([r["accel_mps2"] for r in rows])-g*u
    sigma = np.asarray([r["noise_std_mps2"] for r in rows])
    matrix, bias, drift = np.eye(3), np.zeros(3), np.zeros(3)
    residuals = []
    for axis in range(3):
        X = np.column_stack([np.ones(len(rows)), x, u[:, axis:]])/sigma[:, axis, None]
        Y = y[:, axis]/sigma[:, axis]
        coef = np.linalg.lstsq(X, Y, rcond=None)[0]
        bias[axis], drift[axis] = coef[0], coef[1]/scale
        matrix[axis, axis:] += coef[2:]/g
        residuals.append(Y-X@coef)
    residual = np.asarray(residuals)
    axis = int(np.argmax(np.mean(residual**2, axis=1)))
    rms = float(np.sqrt(np.mean(residual**2)))
    peak = float(np.max(np.abs(residual)))
    prediction = [matrix@(g*np.asarray(s["orientation"])) + bias
                  + drift*(s["temperature_c"]-problem["reference_temperature_c"])
                  for s in problem["prediction_settings"]]
    answer = {"bias_mps2": bias.tolist(), "temperature_drift_mps2_per_c": drift.tolist(),
              "calibration_matrix": matrix.tolist(), "prediction_accel_mps2": np.asarray(prediction).tolist(),
              "diagnosis": "supported", "fault_axis": None, "abstain": False, "confidence": 1.0,
              "evidence_ids": [r["query_id"] for r in rows]}
    return answer, rms, peak, axis


def threshold_answer(fit, rms_threshold, peak_threshold, middle_label, peak_label):
    answer, rms, peak, axis = fit
    label = peak_label if peak > peak_threshold else middle_label if rms > rms_threshold else "supported"
    return {**answer, "diagnosis": label, "abstain": label != "supported",
            "fault_axis": axis if label != "supported" else None}


def shortcut_policy(problem, measure, sequential, *parameters):
    rows = [measure(i) for i in _design(problem, problem["measurement_budget"], sequential=sequential)]
    return threshold_answer(shortcut_fit(problem, rows), *parameters)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Evidence requires Linux with bubblewrap")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Commit source first")
    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, HERE/filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    oracle = load("imu_oracle", "evaluator.py")
    reference = load("imu_reference", "reference_solver.py")
    labels = ("thermal_nonlinearity", "axis_misalignment", "motion_contamination")
    grid_results = {}
    for sequential in (False, True):
        prepared = []
        for spec in oracle.DEVELOPMENT_WORLDS:
            world, problem = oracle._world(spec), oracle.public_problem(spec)
            campaign = oracle._Campaign(world, problem)
            rows = [campaign(i) for i in reference._design(problem, problem["measurement_budget"], sequential=sequential)]
            prepared.append((world, problem, campaign, shortcut_fit(problem, rows)))
        best_score, best_parameters, count = -1, None, 0
        for parameters in itertools.product(np.linspace(.7, 1.8, 10), np.linspace(1.5, 4.5, 10), labels, labels):
            records = []
            # Cache only deterministic public transcripts of fixed trusted probe code.
            # Scoring stays in the oracle; held-out data never enters parameter selection.
            for world, problem, campaign, fit in prepared:
                answer = oracle._validate(threshold_answer(fit, *parameters), campaign)
                records.append({"kind": world["kind"], "valid": True, "abstained": answer["abstain"],
                                "measurements_used": campaign.calls, **oracle._score(world, answer, problem)})
            score = oracle._summary(records)["combined_score"]
            count += 1
            if score > best_score:
                best_score, best_parameters = score, (float(parameters[0]), float(parameters[1]), *parameters[2:])
        grid_results["sequential" if sequential else "designed"] = {
            "policy_count": count, "best_development_score": best_score, "parameters": best_parameters}
    ref_source = (HERE/"reference_solver.py").read_text()
    library = ref_source + "\n" + "\n".join(inspect.getsource(f) for f in (shortcut_fit, threshold_answer, shortcut_policy))
    policies = {"reference": ref_source, "baseline": (HERE.parent/"solution.py").read_text()}
    options = {"six_measurements": {"measurement_limit": 6}, "twelve_measurements": {"measurement_limit": 12},
               "central_temperatures": {"central_only": True}, "sequential_settings": {"sequential": True},
               "diagonal_only": {"diagonal_only": True}}
    options.update({"without_"+label: {"disabled_faults": (label,)} for label in labels})
    for name, options_dict in options.items():
        policies[name] = library + "\ndef infer_imu(problem, measure):\n    return _infer_imu(problem, measure, **%r)\n" % options_dict
    for name, result in grid_results.items():
        policies["threshold_"+name] = library + "\ndef infer_imu(problem, measure):\n    return shortcut_policy(problem, measure, %r, *%r)\n" % (name == "sequential", result["parameters"])
    for name, changes in (("all_abstain", {"abstain": True}), ("never_refuse", {"abstain": False}),
                          ("fixed_axis", {"fault_axis": 0})):
        suffix = "\ndef infer_imu(problem, measure):\n    answer = _infer_imu(problem, measure)\n"
        if name == "fixed_axis":
            suffix += "    if answer['fault_axis'] is not None:\n        answer['fault_axis'] = 0\n"
        else:
            suffix += "    answer.update(%r)\n" % changes
        policies[name] = library+suffix+"    return answer\n"
    report = {"task": TASK_ID, "schema_version": 2,
              "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_tree_clean": True, "execution": "Linux trusted driver and bubblewrap; trusted public-transcript grid",
              "grids": grid_results, "probes": {}}
    with tempfile.TemporaryDirectory(prefix="imu-active-review-") as tmp:
        for name, source in policies.items():
            candidate = Path(tmp)/(name+".py")
            candidate.write_text(source)
            results = []
            for _ in range(2):
                result = subprocess.run([sys.executable, "-m", "sle", "eval", "--allow-uncertified", "--task", TASK_ID,
                                         "--candidate", str(candidate)], cwd=ROOT, capture_output=True, text=True, timeout=480)
                if result.returncode:
                    raise RuntimeError(result.stderr[-2000:])
                results.append(json.loads(result.stdout))
            if results[0] != results[1] or results[0]["valid"] != 1:
                raise AssertionError("invalid or nondeterministic: "+name)
            report["probes"][name] = {"complete_metrics_identical_twice": True, "metrics": results[0]}
            print(name, results[0]["combined_score"], results[0]["heldout_combined_score"], flush=True)
    Path(args.output).write_text(json.dumps(report, indent=2)+"\n")
    for metric in ("combined_score", "heldout_combined_score"):
        for name in ("threshold_designed", "threshold_sequential"):
            if report["probes"][name]["metrics"][metric] >= report["probes"]["reference"]["metrics"][metric]:
                raise AssertionError("shortcut reaches reference: "+name+" "+metric)


if __name__ == "__main__":
    main()
