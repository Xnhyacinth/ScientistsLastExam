"""Exploration engine: exact output distributions of SVT variants with discrete Laplace noise."""
import itertools
import numpy as np

K_SUPPORT = 800


def dlap(b):
    x = np.arange(-K_SUPPORT, K_SUPPORT + 1)
    w = np.exp(-np.abs(x) / b)
    return x, w / w.sum()


def tail_ge(b):
    """G(t) = P(nu >= t) for t in -K..K+1, as a function via lookup."""
    x, p = dlap(b)
    # cumulative from the top
    ge = np.cumsum(p[::-1])[::-1]          # ge[j] = P(nu >= x[j])
    ge = np.concatenate([ge, [0.0]])
    def G(t):
        t = np.asarray(t)
        idx = np.clip(t + K_SUPPORT, 0, 2 * K_SUPPORT + 1)
        out = ge[idx]
        return np.where(t < -K_SUPPORT, 1.0, out)
    return G


def patterns(k, c):
    """All output patterns: strings over TF, stopping after c T's or at length k."""
    out = []
    def rec(prefix, tops):
        if tops == c or len(prefix) == k:
            out.append(prefix)
            return
        rec(prefix + "F", tops)
        rec(prefix + "T", tops + 1)
    rec("", 0)
    return out


class SVT:
    """ρ ~ DLap(b_rho), ν_i ~ DLap(b_nu[i]); T iff q_i + ν_i >= thr + ρ; halt after c T's.
    fast: optional (F, side): side 'up' means q_i >= thr + F gives T with no noise.
    skip: probability η that the whole run is noiseless."""

    def __init__(self, k, c, thr, b_rho, b_nu, fast=None, skip=0.0, refresh=False):
        self.k, self.c, self.thr = k, c, thr
        self.b_rho = b_rho
        self.b_nu = np.broadcast_to(np.asarray(b_nu, float), (k,)).copy()
        self.fast, self.skip, self.refresh = fast, skip, refresh
        self.rho_x, self.rho_p = dlap(b_rho)
        self.G = {b: tail_ge(b) for b in set(self.b_nu.tolist())}
        self.pats = patterns(k, c)

    def _ptop(self, q):
        """ptop[i, r] = P(T at i | rho = rho_x[r])."""
        q = np.asarray(q)
        P = np.empty((self.k, self.rho_x.size))
        for i in range(self.k):
            P[i] = self.G[self.b_nu[i]](self.thr + self.rho_x - q[i])
            if self.fast is not None:
                F, side = self.fast
                if side == "up" and q[i] >= self.thr + F:
                    P[i] = 1.0
                if side == "down" and q[i] <= self.thr - F:
                    P[i] = 0.0
        return P

    def exact_pattern(self, q):
        q = np.asarray(q)
        out = []
        for i in range(self.k):
            out.append("T" if q[i] >= self.thr else "F")
            if out.count("T") == self.c:
                break
        return "".join(out)

    def dist(self, q):
        P = self._ptop(q)
        res = {}
        for pat in self.pats:
            if self.refresh:
                raise NotImplementedError
            f = self.rho_p.copy()
            for i, ch in enumerate(pat):
                f = f * (P[i] if ch == "T" else 1.0 - P[i])
            res[pat] = float(f.sum())
        if self.skip:
            e = self.exact_pattern(q)
            res = {p: (1 - self.skip) * v for p, v in res.items()}
            res[e] += self.skip
        return res


def best_event(d1, d2, delta):
    """max over S of ln((P1(S)-delta)/P2(S)); S is a ratio-sorted prefix (Dinkelbach)."""
    pats = list(d1)
    p1 = np.array([d1[p] for p in pats]); p2 = np.array([d2[p] for p in pats])
    ratio = np.where(p2 > 0, p1 / np.maximum(p2, 1e-300), np.inf)
    order = np.argsort(-ratio)
    A = np.cumsum(p1[order]); B = np.cumsum(p2[order])
    with np.errstate(divide="ignore", invalid="ignore"):
        val = np.where(A > delta, np.log((A - delta) / np.maximum(B, 1e-300)), -np.inf)
        val = np.where((A > delta) & (B <= 0), np.inf, val)
    j = int(np.argmax(val))
    return float(val[j]), [pats[o] for o in order[: j + 1]], float(A[j]), float(B[j])


def loss(mech, q1, q2, delta):
    d1, d2 = mech.dist(q1), mech.dist(q2)
    a = best_event(d1, d2, delta)
    b = best_event(d2, d1, delta)
    return max(a[0], b[0]), (a if a[0] >= b[0] else b)


def sample_dlap(rng, b, size):
    p = 1.0 - np.exp(-1.0 / b)
    return rng.geometric(p, size) - rng.geometric(p, size)


def sample(mech, q, n, rng):
    """Draw n runs; return counts per pattern."""
    q = np.asarray(q)
    rho = sample_dlap(rng, mech.b_rho, n)
    nu = np.stack([sample_dlap(rng, b, n) for b in mech.b_nu], axis=1)
    top = (q[None, :] + nu) >= (mech.thr + rho[:, None])
    if mech.fast is not None:
        F, side = mech.fast
        for i in range(mech.k):
            if side == "up" and q[i] >= mech.thr + F:
                top[:, i] = True
            if side == "down" and q[i] <= mech.thr - F:
                top[:, i] = False
    if mech.skip:
        skip = rng.random(n) < mech.skip
        top[skip] = (q >= mech.thr)[None, :]
    csum = np.cumsum(top, axis=1)
    counts = {}
    for r in range(n):
        row = top[r]; cs = csum[r]
        stop = np.flatnonzero(cs == mech.c)
        L = int(stop[0]) + 1 if stop.size else mech.k
        pat = "".join("T" if t else "F" for t in row[:L])
        counts[pat] = counts.get(pat, 0) + 1
    return counts


def library(k, thr):
    """StatDP-flavoured input pairs: values one step either side of the threshold."""
    A, B = thr + 1, thr - 1
    h = k // 2
    return [
        ([A] + [B] * (k - 1), [A - 1] + [B + 1] * (k - 1)),
        ([B] + [A] * (k - 1), [B + 1] + [A - 1] * (k - 1)),
        ([A] * h + [B] * (k - h), [A - 1] * h + [B + 1] * (k - h)),
        ([B] * h + [A] * (k - h), [B + 1] * h + [A - 1] * (k - h)),
        ([A] * k, [A - 1] * k), ([B] * k, [B + 1] * k),
        ([thr] * k, [thr + 1] * k), ([thr] * k, [thr - 1] * k),
        ([thr] * k, [thr + 1 if i % 2 else thr - 1 for i in range(k)]),
    ]


def p_bottom(b_rho, b_nu, g):
    """P(nu - rho < -g): the chance a correct comparison says F for a query g above threshold."""
    xr, pr = dlap(b_rho)
    G = tail_ge(b_nu)
    return float(np.sum(pr * (1.0 - G(xr - g))))
