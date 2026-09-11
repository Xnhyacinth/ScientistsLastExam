"""Anchors and compliance checks for SparseVectorAudit, on the evaluator's exact engine.

For every world: the best loss found by an exact-objective local search seeded from the library
and from random pairs (the anchor for noise-scale worlds, a sanity bound for compliant ones), the
straddle witness for branch worlds, and the coupling bound eta * (1 + e^epsilon) for the
compliant-branch worlds.

    .venv/bin/python .research/sparse_vector_audit/anchors.py [--starts N] [--iters N]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/ComputerScience/SparseVectorAudit/verification"))
import evaluator as ev  # noqa: E402

T = ev.THRESHOLD


def library(k):
    A, B, h = T + 1, T - 1, k // 2
    return [
        ([A] + [B] * (k - 1), [A - 1] + [B + 1] * (k - 1)),
        ([B] + [A] * (k - 1), [B + 1] + [A - 1] * (k - 1)),
        ([A] * h + [B] * (k - h), [A - 1] * h + [B + 1] * (k - h)),
        ([B] * h + [A] * (k - h), [B + 1] * h + [A - 1] * (k - h)),
        ([A] * k, [A - 1] * k), ([B] * k, [B + 1] * k),
        ([T] * k, [T + 1] * k), ([T] * k, [T - 1] * k),
        ([T] * k, [T + 1 if i % 2 else T - 1 for i in range(k)]),
    ]


def local_search(mech, rng, starts, iters):
    k = mech.k
    seeds = [(np.array(a), np.array(b) - np.array(a)) for a, b in library(k)]
    seeds += [(T + rng.integers(-8, 9, k), rng.integers(-1, 2, k)) for _ in range(starts)]
    best = (-math.inf, None)
    for q, d in seeds:
        q = np.clip(q, ev.QUERY_MIN + 1, ev.QUERY_MAX - 1)
        if not np.any(d):
            d[0] = 1
        cur, ev_ = ev.best_event_loss(mech, q, q + d)
        for _ in range(iters):
            qn, dn = q.copy(), d.copy()
            j = rng.integers(k)
            if rng.random() < 0.5:
                qn[j] = np.clip(qn[j] + rng.choice([-3, -2, -1, 1, 2, 3]), ev.QUERY_MIN + 1, ev.QUERY_MAX - 1)
            else:
                dn[j] = rng.integers(-1, 2)
            if not np.any(dn):
                continue
            v, e = ev.best_event_loss(mech, qn, qn + dn)
            if v >= cur:
                q, d, cur, ev_ = qn, dn, v, e
        if cur > best[0]:
            best = (cur, {"dataset": q.tolist(), "neighbour": (q + d).tolist(), "event": ev_})
    return best


def p_correct_flip(mech, gap, side):
    """Unconditional chance a correct comparison disagrees with the branch at distance gap:
    F for a query gap above the threshold (side up), T for one gap below (side down)."""
    rho = mech.rho
    if side == "up":
        return float(np.sum(mech.rho_p * (1.0 - ev._tail_ge(mech.b_nu, T + rho - (T + gap)))))
    return float(np.sum(mech.rho_p * ev._tail_ge(mech.b_nu, T + rho - (T - gap))))


def straddle(mech):
    offset, side, positions = mech.branch
    k = mech.k
    i = positions[0]
    base = [ev.QUERY_MIN] * k
    if side == "up":
        d = list(base); d[i] = T + offset
        n = list(base); n[i] = T + offset - 1
        event = [p for p in mech.patterns if len(p) > i and p[i] == "F"]
    else:
        d = list(base); d[i] = T - offset
        n = list(base); n[i] = T - offset + 1
        event = [p for p in mech.patterns if len(p) > i and p[i] == "T"]
    return {"dataset": d, "neighbour": n, "event": event}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--starts", type=int, default=24)
    ap.add_argument("--iters", type=int, default=200)
    args = ap.parse_args()
    rng = np.random.default_rng(20260911)
    anchors, report = {}, []
    for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
        mech = ev._Mechanism(spec)
        row = {"name": spec["name"], "kind": spec["kind"], "k": mech.k, "c": mech.c}
        if spec["kind"] == "branch":
            w = straddle(mech)
            loss, p1, p2 = ev.witness_loss(mech, w["dataset"], w["neighbour"], w["event"])
            row.update({"straddle_loss": loss, "straddle_mass": max(p1, p2)})
            anchors[spec["name"]] = w
        else:
            loss, w = local_search(mech, rng, args.starts, args.iters)
            row["search_loss"] = round(loss, 4)
            if spec["kind"] == "noise_scale":
                anchors[spec["name"]] = w
            if spec["kind"] == "compliant_branch":
                offset, side, positions = mech.branch
                flip = p_correct_flip(mech, offset, side)
                eta = flip if (side == "up" and mech.c == 1) else flip * len(positions)
                row.update({"eta": eta, "delta_bound": eta * (1 + math.exp(ev.EPSILON))})
                w2 = straddle(mech)
                l2, p1, p2 = ev.witness_loss(mech, w2["dataset"], w2["neighbour"], w2["event"])
                row.update({"straddle_loss": l2, "straddle_mass": max(p1, p2)})
        report.append(row)
        print(json.dumps(row), flush=True)
    out = ROOT / ".research/sparse_vector_audit/anchors.json"
    out.write_text(json.dumps(anchors, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
