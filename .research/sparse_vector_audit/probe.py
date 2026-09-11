"""Shortcut probe: every strategy an agent could try without the reference's three stages, scored
on both splits. The bar is that the best of them stays below 90 per cent of the reference on the
development split.

    .venv/bin/python .research/sparse_vector_audit/probe.py
"""
import math
import sys
import types
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev, load, TASK  # noqa: E402

ref = load(TASK / "verification/reference_library_scan.py", "sva_ref")
REFUSE = {"verdict": "no_violation", "confidence": 0.5}


def straddle(problem, side, g, pos=0):
    k, t, lo = problem["n_queries"], problem["threshold"], problem["query_min"]
    a, b = [lo] * k, [lo] * k
    want = "F" if side == "up" else "T"
    if side == "up":
        a[pos], b[pos] = t + g - 1, t + g
    else:
        a[pos], b[pos] = t - g + 1, t - g
    return {"verdict": "violation", "dataset": a, "neighbour": b,
            "event": [o for o in problem["output_patterns"] if o[pos:pos + 1] == want], "confidence": 0.9}


def blind(side, g):
    return lambda problem, sample: straddle(problem, side, g)


def pairs_for(problem, library):
    k, t = problem["n_queries"], problem["threshold"]
    if library == "baseline_pair":
        return [([t + 1] + [t - 1] * (k - 1), [t] * k)]
    return ref._library(k, t)


def single_best(delta, c1, n1, c2, n2):
    best, event = -math.inf, []
    for o in set(c1) | set(c2):
        p1, p2 = c1.get(o, 0) / n1, (c2.get(o, 0) + 0.5) / (n2 + 1.0)
        if p1 > delta and math.log((p1 - delta) / p2) > best:
            best, event = math.log((p1 - delta) / p2), [o]
    return best, event


def screen_and_claim(runs, library, mode, tau, scan=False, confirm_alpha=None):
    def audit(problem, sample):
        spent = [0]
        budget = problem["sample_budget"]

        def run(q, n):
            n = int(min(n, budget - spent[0]))
            if n <= 0:
                return None
            spent[0] += n
            return sample(list(q), n)

        if scan:   # the reference's first-query scan, then this strategy
            src = (TASK / "verification/reference_library_scan.py").read_text()
            src = src.replace("    # --- screen the library", "    return {\"verdict\": \"no_violation\", \"_spent\": 0}\n    # --- screen the library", 1)
            mod = types.ModuleType("scan_only"); exec(compile(src, "scan_only", "exec"), mod.__dict__)
            used = [0]

            def counted(q, n):
                used[0] += n
                return sample(q, n)
            out = mod.audit(problem, counted)
            spent[0] += used[0]
            if out["verdict"] == "violation":
                return out
        delta = problem["delta"]
        cache, cands = {}, []
        for a, b in pairs_for(problem, library):
            for q in (a, b):
                if tuple(q) not in cache:
                    c = run(q, runs)
                    if c is None:
                        return REFUSE
                    cache[tuple(q)] = c
            for f, s in ((a, b), (b, a)):
                c1, c2 = cache[tuple(f)], cache[tuple(s)]
                pick = single_best if mode == "single" else ref._plug_in_event
                v, e = pick(delta, c1, runs, c2, runs)
                if e:
                    cands.append((v, f, s, e))
        if not cands:
            return REFUSE
        v, f, s, e = max(cands, key=lambda r: r[0])
        if confirm_alpha is not None:
            n = (budget - spent[0]) // 2
            c1, c2 = run(f, n), run(s, n)
            if c1 is None or c2 is None:
                return REFUSE
            x1, x2 = sum(c1.get(o, 0) for o in e), sum(c2.get(o, 0) for o in e)
            v = ref._certified(delta, x1, n, x2, n, confirm_alpha)
        if v <= tau:
            return REFUSE
        return {"verdict": "violation", "dataset": list(f), "neighbour": list(s), "event": e, "confidence": 0.8}
    return audit


strategies = {}
for side in ("up", "down"):
    for g in range(1, 51):
        strategies["blind_%s_%d" % (side, g)] = blind(side, g)
for runs in (1000, 2000, 4000, 8000, 16000, 24000):
    for library in ("baseline_pair", "library"):
        for mode in ("single", "prefix"):
            for tau in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0):
                if library == "library" and runs > 16000:
                    continue      # eight vectors at this size exceed the budget
                strategies["screen_%d_%s_%s_tau%.2f" % (runs, library, mode, tau)] = screen_and_claim(runs, library, mode, tau)
for runs in (4000, 8000):
    for mode in ("single", "prefix"):
        for tau in (1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
            strategies["scan+screen_%d_%s_tau%.2f" % (runs, mode, tau)] = screen_and_claim(runs, "library", mode, tau, scan=True)
for runs in (2000, 8000, 20000):
    for mode in ("single", "prefix"):
        for alpha in (0.05, 0.2, 0.5):
            strategies["confirm_%d_baseline_pair_%s_a%.2f" % (runs, mode, alpha)] = screen_and_claim(
                runs, "baseline_pair", mode, 1.0, confirm_alpha=alpha)

reference = ev.evaluate(ref.audit)["development_mechanism_score"]
rows = []
for name, audit in strategies.items():
    m = ev.evaluate(audit)
    rows.append((m["development_mechanism_score"], m["heldout_mechanism_score"], m["development_false_discovery_rate"], name))
rows.sort(key=lambda r: (-r[0], -r[1]))
print("strategies %d  reference dev %.4f  bar (90%%) %.4f" % (len(rows), reference, 0.9 * reference))
for dev, held, fdr, name in rows[:25]:
    print("  %-44s dev %.4f  held %.4f  dev fdr %.2f  (%.0f%% of reference)" % (name, dev, held, fdr, 100 * dev / reference))
families = {}
for dev, held, fdr, name in rows:
    fam = name.split("_")[0]
    if fam not in families or dev > families[fam][0]:
        families[fam] = (dev, held, name)
for fam, (dev, held, name) in sorted(families.items()):
    print("family %-14s best dev %.4f held %.4f  %s" % (fam, dev, held, name))
best = rows[0]
print("best %s at %.1f%% of the reference; %d strategies score zero on development" % (
    best[3], 100 * best[0] / reference, sum(1 for r in rows if r[0] == 0.0)))
