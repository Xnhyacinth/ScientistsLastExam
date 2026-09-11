"""Hidden oracle for SparseVectorAudit.

A data curator runs the sparse vector technique, AboveThreshold with a cutoff, over a stream of
counting queries and claims that the implementation is (epsilon, delta)-differentially private.
The candidate audits the claim. It sees the specification the curator says was implemented, and
it may run the implementation on query vectors of its choice, one charged run at a time, under a
budget. It either names a violation, a pair of neighbouring query vectors and a set of outputs
whose probabilities break the claimed inequality, or it declines.

The witness is scored exactly. The oracle knows the implementation, so it computes the two
probabilities of the named event and the privacy loss they imply; nothing about the score is a
statistical estimate. What is uncertain is what the candidate saw: counts from a finite number of
runs. A witness whose true loss does not exceed the claim is a false discovery however good the
counts looked, and it costs one world wherever it is made: zero where declining would have scored
one, minus one where declining scores zero. Without the second half an auditor could publish every
plug-in maximum in the worlds that do violate the claim at no cost, and the confirmation that
separates an audit from a guess would be worth nothing there.

What makes it hard:

    a tight mechanism     the correct implementation with one output above threshold reaches
                          a loss of 0.90 against the claimed epsilon of 1, on events of one to
                          two per cent mass; many pairs and many events, each estimated from
                          counts, will show a loss above the claim somewhere by chance
    delta is part of the  an event of mass below delta can have any ratio at all and still not
    claim                 break (epsilon, delta); in the compliant-branch worlds the
                          implementation deviates from the specification exactly there, where a
                          pure-DP auditor sees an infinite ratio
    small events          the noise-scale bugs break the claim only on events of well under one
                          per cent mass on one side, so certifying them costs tens of thousands
                          of runs, and the budget is shared with the search
    a data-dependent      the branch bugs skip the noise for queries far from the threshold, an
    branch                optimisation that looks harmless; the violation lives on one pair that
                          straddles an unpublished offset at an unpublished set of positions,
                          and inputs near the threshold never reach it
"""
from __future__ import annotations

import math
import zlib

import numpy as np

EPSILON = 1.0
DELTA = 1e-3
THRESHOLD = 50
QUERY_MIN = 0
QUERY_MAX = 100
SAMPLE_BUDGET = 200_000
MAX_SAMPLES_PER_CALL = 200_000
EPS_CAP = 2.0 * EPSILON          # a witness at twice the claimed epsilon is full credit
K_SUPPORT = 1200                 # discrete Laplace support truncation for the exact computation

WORLD_KINDS = ("compliant", "compliant_branch", "noise_scale", "branch")
REFUSAL_KINDS = ("compliant", "compliant_branch")

_PMF = {}
_TAIL = {}


def _dlap(b):
    if b not in _PMF:
        x = np.arange(-K_SUPPORT, K_SUPPORT + 1)
        w = np.exp(-np.abs(x) / b)
        _PMF[b] = w / w.sum()
    return _PMF[b]


def _tail_ge(b, t):
    """P(nu >= t) for nu ~ DLap(b), t an integer array."""
    if b not in _TAIL:
        p = _dlap(b)
        _TAIL[b] = np.concatenate([np.cumsum(p[::-1])[::-1], [0.0]])
    ge = _TAIL[b]
    t = np.asarray(t)
    return np.where(t < -K_SUPPORT, 1.0, ge[np.clip(t + K_SUPPORT, 0, 2 * K_SUPPORT + 1)])


def _patterns(k, c):
    out = []

    def rec(prefix, tops):
        if tops == c or len(prefix) == k:
            out.append(prefix)
            return
        rec(prefix + "F", tops)
        rec(prefix + "T", tops + 1)

    rec("", 0)
    return out


def _intended_scales(c):
    eps1 = eps2 = EPSILON / 2.0
    return 1.0 / eps1, 2.0 * c / eps2


class _Mechanism:
    """The implementation behind one world. The specification is AboveThreshold with a cutoff:
    rho ~ DLap(2/epsilon), nu_i ~ DLap(4c/epsilon), output T for query i when q_i + nu_i >=
    threshold + rho, halt after c outputs T. A world's implementation may scale a noise wrongly
    or skip the noise for queries far from the threshold at some positions."""

    def __init__(self, spec):
        self.k = int(spec["k"])
        self.c = int(spec["c"])
        b_rho, b_nu = _intended_scales(self.c)
        self.b_rho = b_rho * float(spec.get("rho_factor", 1.0))
        self.b_nu = b_nu * float(spec.get("nu_factor", 1.0))
        branch = spec.get("branch")
        if branch is None:
            self.branch = None
        else:
            self.branch = (int(branch["offset"]), branch["side"], tuple(int(i) for i in branch["positions"]))
        self.patterns = _patterns(self.k, self.c)
        self.index = {p: j for j, p in enumerate(self.patterns)}
        self.rho = np.arange(-K_SUPPORT, K_SUPPORT + 1)
        self.rho_p = _dlap(self.b_rho)

    def _forced(self, q):
        """-1 where the query is computed as specified, 1 or 0 where a branch forces T or F."""
        forced = np.full(self.k, -1)
        if self.branch is not None:
            offset, side, positions = self.branch
            for i in positions:
                if side == "up" and q[i] >= THRESHOLD + offset:
                    forced[i] = 1
                elif side == "down" and q[i] <= THRESHOLD - offset:
                    forced[i] = 0
        return forced

    def distribution(self, q):
        q = np.asarray(q, dtype=np.int64)
        forced = self._forced(q)
        top = np.empty((self.k, self.rho.size))
        for i in range(self.k):
            if forced[i] == 1:
                top[i] = 1.0
            elif forced[i] == 0:
                top[i] = 0.0
            else:
                top[i] = _tail_ge(self.b_nu, THRESHOLD + self.rho - q[i])
        out = np.empty(len(self.patterns))
        for j, pat in enumerate(self.patterns):
            f = self.rho_p
            for i, ch in enumerate(pat):
                f = f * (top[i] if ch == "T" else 1.0 - top[i])
            out[j] = f.sum()
        return out

    def sample(self, q, n, rng):
        q = np.asarray(q, dtype=np.int64)

        def dlap(b, size):
            p = 1.0 - math.exp(-1.0 / b)
            return rng.geometric(p, size) - rng.geometric(p, size)

        rho = dlap(self.b_rho, n)
        nu = dlap(self.b_nu, (n, self.k))
        top = (q[None, :] + nu) >= (THRESHOLD + rho[:, None])
        forced = self._forced(q)
        top[:, forced == 1] = True
        top[:, forced == 0] = False
        csum = np.cumsum(top, axis=1)
        reached = csum >= self.c
        length = np.where(reached.any(axis=1), reached.argmax(axis=1) + 1, self.k)
        weights = (1 << np.arange(self.k, dtype=np.int64))
        mask = np.arange(self.k)[None, :] < length[:, None]
        code = ((top & mask).astype(np.int64) * weights[None, :]).sum(axis=1) * 64 + length
        codes, counts = np.unique(code, return_counts=True)
        result = {}
        for cd, ct in zip(codes.tolist(), counts.tolist()):
            L, bits = cd % 64, cd // 64
            result["".join("T" if (bits >> i) & 1 else "F" for i in range(L))] = int(ct)
        return result


def _implied_loss(p1, p2):
    """ln((p1 - delta) / p2), with the conventions the claim implies."""
    if p1 <= DELTA:
        return -math.inf
    if p2 <= 0.0:
        return math.inf
    return math.log((p1 - DELTA) / p2)


def witness_loss(mechanism, dataset, neighbour, event):
    """The exact privacy loss a witness certifies: the larger of its two orders."""
    d1 = mechanism.distribution(dataset)
    d2 = mechanism.distribution(neighbour)
    idx = [mechanism.index[p] for p in event]
    p1, p2 = float(d1[idx].sum()), float(d2[idx].sum())
    return max(_implied_loss(p1, p2), _implied_loss(p2, p1)), p1, p2


def best_event_loss(mechanism, dataset, neighbour):
    """The largest loss any event certifies for a fixed pair: a ratio-sorted prefix of the
    outputs is optimal for (p1(S) - delta) / p2(S) by the Dinkelbach argument."""
    d1 = mechanism.distribution(dataset)
    d2 = mechanism.distribution(neighbour)
    best = (-math.inf, [])
    for a, b in ((d1, d2), (d2, d1)):
        with np.errstate(divide="ignore"):
            ratio = np.where(b > 0, a / np.maximum(b, 1e-300), np.inf)
        order = np.argsort(-ratio, kind="stable")
        A, B = np.cumsum(a[order]), np.cumsum(b[order])
        for j in range(len(order)):
            v = _implied_loss(float(A[j]), float(B[j]))
            if v > best[0]:
                best = (v, [mechanism.patterns[o] for o in order[: j + 1]])
    return best


_WORLDS = {}


def _world(spec):
    key = spec["name"]
    if key not in _WORLDS:
        mechanism = _Mechanism(spec)
        anchor = spec.get("anchor")
        anchor_loss = None
        if anchor is not None:
            anchor_loss = witness_loss(mechanism, anchor["dataset"], anchor["neighbour"], anchor["event"])[0]
        _WORLDS[key] = {"spec": spec, "kind": spec["kind"], "mechanism": mechanism,
                        "anchor_loss": anchor_loss, "budget": int(spec.get("budget", SAMPLE_BUDGET))}
    return _WORLDS[key]


class _Campaign:
    """The candidate's only access to the implementation. The candidate receives the closure,
    not this object, so the ledger is out of its reach. Draws are seeded by the world, the query
    vector and how many times that vector has been run before, so a candidate's counts do not
    depend on the order of its calls."""

    def __init__(self, world):
        self.world = world
        self.budget = world["budget"]
        self.spent = 0
        self.calls = {}
        self.violated = False

    def oracle(self):
        world, state = self.world, self
        mechanism = world["mechanism"]
        seed = int(world["spec"]["seed"])

        def sample(queries, n):
            if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
                raise ValueError("n must be an integer")
            n = int(n)
            if not 1 <= n <= MAX_SAMPLES_PER_CALL:
                raise ValueError("n must lie in 1..%d" % MAX_SAMPLES_PER_CALL)
            q = _query_vector(queries, mechanism.k)
            if state.spent + n > state.budget:
                state.violated = True
                raise RuntimeError("sample budget exhausted")
            state.spent += n
            key = tuple(q.tolist())
            count = state.calls.get(key, 0)
            state.calls[key] = count + 1
            rng = np.random.default_rng([seed, zlib.crc32(q.astype(np.int64).tobytes()), count])
            return mechanism.sample(q, n, rng)

        return sample


def _query_vector(queries, k):
    if not isinstance(queries, (list, tuple)) or len(queries) != k:
        raise ValueError("a query vector is a list of %d integers" % k)
    out = []
    for v in queries:
        if isinstance(v, bool) or not isinstance(v, (int, np.integer)):
            raise ValueError("query answers must be integers")
        v = int(v)
        if not QUERY_MIN <= v <= QUERY_MAX:
            raise ValueError("query answers must lie in %d..%d" % (QUERY_MIN, QUERY_MAX))
        out.append(v)
    return np.asarray(out, dtype=np.int64)


ALGORITHM = (
    "rho = DLap(threshold_noise_scale); count = 0; for i in 0..n_queries-1: "
    "nu_i = DLap(query_noise_scale); if q_i + nu_i >= threshold + rho: output T, count += 1, "
    "and halt if count == cutoff; else output F. The threshold noise is drawn once and is not "
    "redrawn after an output T. The output is the string of T and F emitted before halting.")

PUBLIC_PROBLEM = {
    "n_queries": None,
    "cutoff": None,
    "threshold": THRESHOLD,
    "query_min": QUERY_MIN,
    "query_max": QUERY_MAX,
    "epsilon": EPSILON,
    "delta": DELTA,
    "threshold_noise_scale": None,
    "query_noise_scale": None,
    "sample_budget": SAMPLE_BUDGET,
    "output_patterns": None,
    "algorithm": ALGORITHM,
    "noise_model": "DLap(b) is the discrete Laplace distribution on the integers with probability "
                   "proportional to exp(-|x| / b); every draw is independent",
    "adjacency": "two query vectors are neighbours when they differ and every answer differs by at "
                 "most one, in either direction, independently per query: each query is a "
                 "counting query of sensitivity one, and a neighbouring dataset may move "
                 "different queries in different directions",
    "claim": "the curator claims that for every pair of neighbouring query vectors q and q' "
             "and every set S of outputs, P[M(q) in S] <= exp(epsilon) * P[M(q') in S] + delta",
    "implementation_model": "the specification above is what the curator says was implemented; "
                            "sample runs the implementation actually deployed, which may or may "
                            "not be the specification",
    "sample_model": "sample(queries, n) runs the deployed implementation n times on the query "
                    "vector, independently, and returns a mapping from output string to count; "
                    "it charges n runs against sample_budget",
    "answer_format": "verdict is violation or no_violation; a violation names dataset and "
                     "neighbour, two neighbouring query vectors, and event, a list of output "
                     "strings, such that the claim's inequality fails for that pair and that "
                     "event in one of the two orders",
}


def _public_problem(world):
    spec = world["spec"]
    k, c = int(spec["k"]), int(spec["c"])
    b_rho, b_nu = _intended_scales(c)
    problem = dict(PUBLIC_PROBLEM)
    problem.update({
        "n_queries": k,
        "cutoff": c,
        "threshold_noise_scale": b_rho,
        "query_noise_scale": b_nu,
        "sample_budget": world["budget"],
        "output_patterns": list(world["mechanism"].patterns),
    })
    return problem


def _validate_submission(submission, mechanism):
    if not isinstance(submission, dict):
        raise ValueError("submission must be a mapping")
    confidence = float(submission.get("confidence", 0.0))
    if not math.isfinite(confidence):
        raise ValueError("confidence must be finite")
    confidence = float(np.clip(confidence, 0.0, 1.0))
    if submission.get("abstain", False) is True:
        return None, confidence
    verdict = submission.get("verdict")
    if verdict == "no_violation":
        return None, confidence
    if verdict != "violation":
        raise ValueError("verdict must be 'violation' or 'no_violation'")
    dataset = _query_vector(submission.get("dataset"), mechanism.k)
    neighbour = _query_vector(submission.get("neighbour"), mechanism.k)
    diff = np.abs(dataset - neighbour)
    if diff.max() == 0 or diff.max() > 1:
        raise ValueError("dataset and neighbour must be neighbours")
    event = submission.get("event")
    if not isinstance(event, (list, tuple)) or not event:
        raise ValueError("event must be a non-empty list of output strings")
    names = []
    for p in event:
        if not isinstance(p, str) or p not in mechanism.index:
            raise ValueError("event lists something that is not an output string")
        names.append(p)
    if len(set(names)) != len(names):
        raise ValueError("event lists an output twice")
    return (dataset, neighbour, names), confidence


def _metrics(world, witness):
    blank = {"witness_loss": None, "witness_strength": 0.0, "mechanism_score": 0.0,
             "false_discovery": False, "correct_refusal": False}
    refusal_world = world["kind"] in REFUSAL_KINDS
    if witness is None:
        blank.update({"mechanism_score": 1.0 if refusal_world else 0.0,
                      "correct_refusal": refusal_world})
        return blank
    loss, _p1, _p2 = witness_loss(world["mechanism"], *witness)
    blank["witness_loss"] = None if not math.isfinite(loss) else round(loss, 6)
    if loss <= EPSILON or refusal_world:
        # A witness that does not break the claim is a false discovery, and in a compliant
        # world every witness is one (the second test is unreachable while the compliance
        # proofs hold). A false witness costs one world wherever it is made: it scores zero
        # where declining would have scored one, and minus one where declining scores zero.
        blank["false_discovery"] = True
        blank["mechanism_score"] = 0.0 if refusal_world else -1.0
        return blank
    top = min(world["anchor_loss"], EPS_CAP)
    strength = float(np.clip((min(loss, EPS_CAP) - EPSILON) / (top - EPSILON), 0.0, 1.0))
    blank.update({"witness_strength": strength, "mechanism_score": strength})
    return blank


# The worlds. Every world's public problem is the same specification with its own number of
# queries and cutoff; what differs is the implementation behind `sample`. Anchors are witnesses
# found by the builder's exact search (.research/sparse_vector_audit/anchors.py); the evaluator
# recomputes their loss, so the normalisation is re-derived on every run.
ALL = None   # every position


def _w(name, kind, seed, k, c, **extra):
    spec = {"name": name, "kind": kind, "seed": seed, "k": k, "c": c}
    branch = extra.pop("branch", None)
    if branch is not None:
        offset, side, positions = branch
        spec["branch"] = {"offset": offset, "side": side,
                          "positions": list(range(k)) if positions is ALL else list(positions)}
    spec.update(extra)
    spec["anchor"] = ANCHORS.get(name)
    return spec


ANCHORS = {
    "dev-noise-a": {"dataset": [49, 49, 50, 50, 49, 48, 50, 46, 50, 69], "neighbour": [50, 50, 51, 51, 50, 49, 49, 45, 49, 69],
        "event": ["FFFFFFT"]},
    "dev-noise-b": {"dataset": [50, 49, 49, 49, 49, 49, 49, 50, 43, 47], "neighbour": [49, 50, 50, 50, 50, 50, 50, 49, 43, 48],
        "event": ["TFFFFFFT"]},
    "dev-noise-c": {"dataset": [49, 49, 49, 49, 49, 49, 49, 49, 50, 46], "neighbour": [50, 50, 50, 50, 50, 50, 50, 50, 49, 47],
        "event": ["FFFFFFFFT"]},
    "dev-branch-a": {"dataset": [62, 0, 0, 0, 0, 0, 0, 0, 0, 0], "neighbour": [61, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "event": [
            "FFFFFFFFFF", "FFFFFFFFFT", "FFFFFFFFT", "FFFFFFFT", "FFFFFFT", "FFFFFT",
            "FFFFT", "FFFT", "FFT", "FT",
        ]},
    "dev-branch-b": {"dataset": [78, 0, 0, 0, 0, 0, 0, 0, 0, 0], "neighbour": [77, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "event": [
            "FFFFFFFFFF", "FFFFFFFFFT", "FFFFFFFFTF", "FFFFFFFFTT", "FFFFFFFTFF", "FFFFFFFTFT",
            "FFFFFFFTTF", "FFFFFFFTTT", "FFFFFFTFFF", "FFFFFFTFFT", "FFFFFFTFTF", "FFFFFFTFTT",
            "FFFFFFTTFF", "FFFFFFTTFT", "FFFFFFTTT", "FFFFFTFFFF", "FFFFFTFFFT", "FFFFFTFFTF",
            "FFFFFTFFTT", "FFFFFTFTFF", "FFFFFTFTFT", "FFFFFTFTT", "FFFFFTTFFF", "FFFFFTTFFT",
            "FFFFFTTFT", "FFFFFTTT", "FFFFTFFFFF", "FFFFTFFFFT", "FFFFTFFFTF", "FFFFTFFFTT",
            "FFFFTFFTFF", "FFFFTFFTFT", "FFFFTFFTT", "FFFFTFTFFF", "FFFFTFTFFT", "FFFFTFTFT",
            "FFFFTFTT", "FFFFTTFFFF", "FFFFTTFFFT", "FFFFTTFFT", "FFFFTTFT", "FFFFTTT",
            "FFFTFFFFFF", "FFFTFFFFFT", "FFFTFFFFTF", "FFFTFFFFTT", "FFFTFFFTFF", "FFFTFFFTFT",
            "FFFTFFFTT", "FFFTFFTFFF", "FFFTFFTFFT", "FFFTFFTFT", "FFFTFFTT", "FFFTFTFFFF",
            "FFFTFTFFFT", "FFFTFTFFT", "FFFTFTFT", "FFFTFTT", "FFFTTFFFFF", "FFFTTFFFFT",
            "FFFTTFFFT", "FFFTTFFT", "FFFTTFT", "FFFTTT", "FFTFFFFFFF", "FFTFFFFFFT",
            "FFTFFFFFTF", "FFTFFFFFTT", "FFTFFFFTFF", "FFTFFFFTFT", "FFTFFFFTT", "FFTFFFTFFF",
            "FFTFFFTFFT", "FFTFFFTFT", "FFTFFFTT", "FFTFFTFFFF", "FFTFFTFFFT", "FFTFFTFFT",
            "FFTFFTFT", "FFTFFTT", "FFTFTFFFFF", "FFTFTFFFFT", "FFTFTFFFT", "FFTFTFFT",
            "FFTFTFT", "FFTFTT", "FFTTFFFFFF", "FFTTFFFFFT", "FFTTFFFFT", "FFTTFFFT",
            "FFTTFFT", "FFTTFT", "FFTTT", "FTFFFFFFFF", "FTFFFFFFFT", "FTFFFFFFTF",
            "FTFFFFFFTT", "FTFFFFFTFF", "FTFFFFFTFT", "FTFFFFFTT", "FTFFFFTFFF", "FTFFFFTFFT",
            "FTFFFFTFT", "FTFFFFTT", "FTFFFTFFFF", "FTFFFTFFFT", "FTFFFTFFT", "FTFFFTFT",
            "FTFFFTT", "FTFFTFFFFF", "FTFFTFFFFT", "FTFFTFFFT", "FTFFTFFT", "FTFFTFT",
            "FTFFTT", "FTFTFFFFFF", "FTFTFFFFFT", "FTFTFFFFT", "FTFTFFFT", "FTFTFFT",
            "FTFTFT", "FTFTT", "FTTFFFFFFF", "FTTFFFFFFT", "FTTFFFFFT", "FTTFFFFT",
            "FTTFFFT", "FTTFFT", "FTTFT", "FTTT",
        ]},
    "dev-branch-c": {"dataset": [0, 0, 0, 0, 0, 41, 0, 0, 0, 0], "neighbour": [0, 0, 0, 0, 0, 42, 0, 0, 0, 0],
        "event": ["FFFFFT"]},
    "dev-branch-d": {"dataset": [0, 0, 0, 0, 0, 0, 0, 68, 0, 0, 0, 0], "neighbour": [0, 0, 0, 0, 0, 0, 0, 67, 0, 0, 0, 0],
        "event": [
            "FFFFFFFFFFFF", "FFFFFFFFFFFT", "FFFFFFFFFFTF", "FFFFFFFFFFTT", "FFFFFFFFFTFF", "FFFFFFFFFTFT",
            "FFFFFFFFFTT", "FFFFFFFFTFFF", "FFFFFFFFTFFT", "FFFFFFFFTFT", "FFFFFFFFTT", "FFFFFFTFFFFF",
            "FFFFFFTFFFFT", "FFFFFFTFFFT", "FFFFFFTFFT", "FFFFFFTFT", "FFFFFTFFFFFF", "FFFFFTFFFFFT",
            "FFFFFTFFFFT", "FFFFFTFFFT", "FFFFFTFFT", "FFFFTFFFFFFF", "FFFFTFFFFFFT", "FFFFTFFFFFT",
            "FFFFTFFFFT", "FFFFTFFFT", "FFFTFFFFFFFF", "FFFTFFFFFFFT", "FFFTFFFFFFT", "FFFTFFFFFT",
            "FFFTFFFFT", "FFTFFFFFFFFF", "FFTFFFFFFFFT", "FFTFFFFFFFT", "FFTFFFFFFT", "FFTFFFFFT",
            "FTFFFFFFFFFF", "FTFFFFFFFFFT", "FTFFFFFFFFT", "FTFFFFFFFT", "FTFFFFFFT", "TFFFFFFFFFFF",
            "TFFFFFFFFFFT", "TFFFFFFFFFT", "TFFFFFFFFT", "TFFFFFFFT",
        ]},
    "held-noise-a": {"dataset": [49, 49, 50, 50, 50, 50, 50, 50, 49, 49], "neighbour": [50, 50, 49, 49, 49, 49, 49, 49, 50, 50],
        "event": ["TTFFFFFFT", "FTFFFFFFTT", "TFFFFFFFTT", "TTFFFFFFFT"]},
    "held-noise-b": {"dataset": [49, 48, 50, 50, 50, 49, 50, 61, 55], "neighbour": [50, 49, 51, 51, 51, 50, 49, 60, 56],
        "event": ["FFFFFFT"]},
    "held-branch-a": {"dataset": [0, 0, 0, 0, 65, 0, 0, 0, 0, 0], "neighbour": [0, 0, 0, 0, 64, 0, 0, 0, 0, 0],
        "event": ["FFFFFFFFFF", "FFFFFFFFFT", "FFFFFFFFT", "FFFFFFFT", "FFFFFFT", "FFFFFT"]},
    "held-branch-b": {"dataset": [30, 0, 0, 0, 0, 0, 0, 0, 0, 0], "neighbour": [31, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "event": [
            "TFFFFFFFFF", "TFFFFFFFFT", "TFFFFFFFT", "TFFFFFFT", "TFFFFFT", "TFFFFT",
            "TFFFT", "TFFT", "TFT", "TT",
        ]},
}

DEVELOPMENT_WORLDS = (
    _w("dev-compliant-a", "compliant", 73100101, 10, 1),
    _w("dev-compliant-b", "compliant", 73100102, 12, 1),
    _w("dev-compliant-c", "compliant", 73100103, 8, 2),
    _w("dev-compliant-branch-a", "compliant_branch", 73100104, 10, 1, branch=(34, "up", ALL)),
    _w("dev-compliant-branch-b", "compliant_branch", 73100105, 10, 1, branch=(42, "down", (3, 4, 5, 6))),
    _w("dev-noise-a", "noise_scale", 73100106, 10, 1, nu_factor=0.5),
    _w("dev-noise-b", "noise_scale", 73100107, 10, 2, nu_factor=0.5),
    _w("dev-noise-c", "noise_scale", 73100108, 10, 1, rho_factor=0.5),
    _w("dev-branch-a", "branch", 73100109, 10, 1, branch=(12, "up", ALL)),
    _w("dev-branch-b", "branch", 73100110, 10, 3, branch=(28, "up", ALL)),
    _w("dev-branch-c", "branch", 73100111, 10, 1, branch=(9, "down", (5, 6, 7, 8, 9))),
    _w("dev-branch-d", "branch", 73100112, 12, 2, branch=(18, "up", (7, 9, 11))),
)

HELDOUT_WORLDS = (
    _w("held-compliant-a", "compliant", 84200201, 11, 1),
    _w("held-compliant-branch-a", "compliant_branch", 84200202, 10, 1, branch=(36, "up", (2, 3, 4, 5, 6, 7))),
    _w("held-noise-a", "noise_scale", 84200203, 10, 3, nu_factor=1.0 / 3.0),
    _w("held-noise-b", "noise_scale", 84200204, 9, 1, nu_factor=0.6),
    _w("held-branch-a", "branch", 84200205, 10, 1, branch=(15, "up", (4, 5))),
    _w("held-branch-b", "branch", 84200206, 10, 2, branch=(20, "down", ALL)),
)

ROW_KEYS = ("witness_strength", "mechanism_score", "false_discovery", "correct_refusal")


def _evaluate_world(audit, spec, split, index):
    world = _world(spec)
    campaign = _Campaign(world)
    problem = _public_problem(world)
    base = {"split": split, "world_index": int(index), "kind": world["kind"], "samples_used": 0}
    try:
        reset = getattr(audit, "reset_session", None)
        if callable(reset):
            reset()
        submission = audit(problem, campaign.oracle())
        witness, confidence = _validate_submission(submission, world["mechanism"])
        if campaign.violated:
            raise RuntimeError("sample budget exceeded")
        metrics = _metrics(world, witness)
        target = max(metrics["mechanism_score"], 0.0)
        row = dict(base)
        row.update({key: metrics[key] for key in ROW_KEYS})
        row.update({
            "valid": True,
            "abstained": witness is None,
            "witness_loss": metrics["witness_loss"],
            "confidence": round(confidence, 6),
            "confidence_calibration_score": round(1.0 - (confidence - target) ** 2, 6),
            "samples_used": campaign.spent,
        })
        for key in ("witness_strength", "mechanism_score"):
            row[key] = round(float(row[key]), 6)
        return row
    except Exception as exc:  # noqa: BLE001 - a bad candidate scores zero, it does not crash this
        row = dict(base)
        row.update({key: (0.0 if key.endswith(("_score", "_strength")) else False) for key in ROW_KEYS})
        row.update({
            "valid": False,
            "reason": "%s: %s" % (type(exc).__name__, exc),
            "abstained": True,
            "witness_loss": None,
            "confidence": 0.0,
            "confidence_calibration_score": 0.0,
            "samples_used": campaign.spent,
        })
        return row


def _split_summary(records):
    determinable = [r for r in records if r["kind"] not in REFUSAL_KINDS]
    unsupported = [r for r in records if r["kind"] in REFUSAL_KINDS]
    raw = float(np.mean([r["mechanism_score"] for r in records]))
    claims = [r for r in records if r["valid"] and not r["abstained"]]
    false_claims = sum(bool(r["false_discovery"]) for r in claims)
    always_abstain = len(unsupported) / len(records)
    normalized = float(np.clip((raw - always_abstain) / (1.0 - always_abstain), 0.0, 1.0))
    return {
        "normalized_mechanism": normalized,
        "raw_mechanism": raw,
        "witness_strength": float(np.mean([r["witness_strength"] for r in determinable])),
        "false_discovery_rate": false_claims / max(1, len(claims)),
        "false_discovery_count": false_claims,
        "false_discovery_denominator": len(claims),
        "all_world_false_claim_fraction": false_claims / len(records),
        "witness_strength_sum": sum(r["witness_strength"] for r in determinable),
        "witness_strength_denominator": len(determinable),
        "correct_refusal_count": sum(bool(r["correct_refusal"]) for r in unsupported),
        "correct_refusal_denominator": len(unsupported),
        "discovery_count": sum(r["valid"] and not r["abstained"] for r in determinable),
        "discovery_denominator": len(determinable),
        "correct_refusal_rate": float(np.mean([r["correct_refusal"] for r in unsupported])),
        "discovery_coverage": float(np.mean([not r["abstained"] for r in determinable])),
        "confidence_calibration": float(np.mean([r["confidence_calibration_score"] for r in records])),
        "mean_samples_used": float(np.mean([r["samples_used"] for r in records])),
        "valid_count": sum(bool(r["valid"]) for r in records),
        "world_count": len(records),
    }


def evaluate(audit):
    development = [_evaluate_world(audit, spec, "development", index)
                   for index, spec in enumerate(DEVELOPMENT_WORLDS)]
    heldout = [_evaluate_world(audit, spec, "heldout", index)
               for index, spec in enumerate(HELDOUT_WORLDS)]
    dev = _split_summary(development)
    held = _split_summary(heldout)
    valid = float(dev["valid_count"] == dev["world_count"] and held["valid_count"] == held["world_count"])
    return {
        "combined_score": dev["normalized_mechanism"] if valid else 0.0,
        "valid": valid,
        "feasibility_rate": dev["valid_count"] / dev["world_count"],
        "raw_score": dev["normalized_mechanism"] if valid else 0.0,
        "development_mechanism_score": dev["normalized_mechanism"],
        "development_raw_mechanism": dev["raw_mechanism"],
        "development_witness_strength": dev["witness_strength"],
        "development_false_discovery_rate": dev["false_discovery_rate"],
        "development_correct_refusal_rate": dev["correct_refusal_rate"],
        "development_discovery_coverage": dev["discovery_coverage"],
        "development_confidence_calibration": dev["confidence_calibration"],
        "development_mean_samples_used": dev["mean_samples_used"],
        # Evaluator-only: the sealed split is removed from the search-visible metric view by the
        # visibility contract, so a searcher cannot steer on it.
        "heldout_mechanism_score": held["normalized_mechanism"],
        "heldout_witness_strength": held["witness_strength"],
        "heldout_false_discovery_rate": held["false_discovery_rate"],
        "heldout_correct_refusal_rate": held["correct_refusal_rate"],
        "heldout_discovery_coverage": held["discovery_coverage"],
        **{split + "_" + key: summary[key]
           for split, summary in (("development", dev), ("heldout", held))
           for key in ("false_discovery_count", "false_discovery_denominator",
                       "all_world_false_claim_fraction", "witness_strength_sum", "witness_strength_denominator",
                       "correct_refusal_count", "correct_refusal_denominator", "discovery_count",
                       "discovery_denominator", "valid_count", "world_count")},
        "per_instance": development + heldout,
    }
