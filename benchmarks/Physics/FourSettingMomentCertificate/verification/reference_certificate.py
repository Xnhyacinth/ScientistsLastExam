"""Public-input SOS search adapted from BellBoundCertificate's rational repair solver.

The basis uses the permitted mixed-party moment pool. Numerical optimization only proposes
coefficients; exact rational repair and LDL squares produce the submitted proof.
"""
from __future__ import annotations
import math
from fractions import Fraction
import numpy as np
from scipy.optimize import minimize

def reduce_side(letters) -> tuple:
    """Free reduction under X_i^2 = I."""
    out: list = []
    for x in letters:
        if out and out[-1] == x:
            out.pop()
        else:
            out.append(x)
    return tuple(out)


def canonical(a, b) -> tuple:
    return (reduce_side(a), reduce_side(b))


def dagger(word: tuple) -> tuple:
    a, b = word
    return (tuple(reversed(a)), tuple(reversed(b)))


def multiply(u: tuple, v: tuple) -> tuple:
    """u * v, using [A_x, B_y] = 0 to keep the A-part and B-part separate."""
    return canonical(u[0] + v[0], u[1] + v[1])


def is_positive_semidefinite(matrix, size) -> bool:
    """Exact PSD test by symmetric Gaussian elimination with diagonal pivoting.

    Each step takes the Schur complement about the largest remaining diagonal entry, which keeps
    the working matrix symmetric and never needs a square root. A negative pivot exhibits a
    direction of negative curvature. A zero pivot is admissible only when the entire remaining
    block vanishes: if the largest remaining diagonal entry is zero but some off-diagonal entry
    is not, the two-by-two minor through it has determinant ``-m^2 < 0``.

    The caller has already bounded the size and the entry magnitudes, so the rationals cannot
    grow without limit.
    """
    work = [[Fraction(value) for value in row] for row in matrix]
    for k in range(size):
        pivot_row = max(range(k, size), key=lambda r: work[r][r])
        if work[pivot_row][pivot_row] < 0:
            return False
        if work[pivot_row][pivot_row] == 0:
            return all(work[r][c] == 0 for r in range(k, size) for c in range(k, size))
        work[k], work[pivot_row] = work[pivot_row], work[k]
        for r in range(size):
            work[r][k], work[r][pivot_row] = work[r][pivot_row], work[r][k]
        pivot = work[k][k]
        for r in range(k + 1, size):
            factor = work[r][k]
            if factor == 0:
                continue
            factor = factor / pivot
            for c in range(k + 1, size):
                work[r][c] -= factor * work[k][c]
    return True


def word_groups(basis):
    """Which (i, j) cells contribute to each canonical word."""
    groups = {}
    for i, s in enumerate(basis):
        ds = dagger(s)
        for j, t in enumerate(basis):
            groups.setdefault(multiply(ds, t), []).append((i, j))
    return groups


def _group_index(basis, groups):
    """Map every (i, j) cell to the index of the canonical word it contributes to.

    With this, a group sum is one `np.bincount` and the matrix `sum_g c_g C_g` is one fancy-index
    reshape, which is what makes an analytic gradient cheap enough to matter: L-BFGS without a
    gradient finite-differences every one of the |basis|^2 variables per step, and on the 16-word
    I3322 basis that alone was most of nine minutes.
    """
    size = len(basis)
    order = list(groups)
    position = {word: k for k, word in enumerate(order)}
    index = np.empty(size * size, dtype=np.int64)
    for word, cells in groups.items():
        for i, j in cells:
            index[i * size + j] = position[word]
    return order, index


def _factored_solution(functional, basis, groups, seed=0, restarts=3):
    """Minimise the bound over Q = R^T R, with the operator identity as a rising penalty.

    Writing Q as R^T R makes positive semidefiniteness structural, so the only thing left to
    enforce is the identity, and a quasi-Newton method walks it down far more accurately than
    alternating projections do near the cone boundary - 1e-7 from Tsirelson's bound on CHSH
    against 4e-2 for Dykstra on the same basis. Accuracy is what makes the certificate cheap: the
    diagonal shift that buys positive semidefiniteness back after rounding is charged straight to
    the bound, so a point accurate to 1e-9 costs about |basis| * 1e-9 and one accurate to 1e-2
    costs ten million times that.
    """
    size = len(basis)
    identity = ((), ())
    order, index = _group_index(basis, groups)
    count = len(order)
    target = np.zeros(count)
    for word, coefficient in functional.items():
        if word not in groups:
            raise KeyError("functional word %r is outside the products of this basis" % (word,))
        target[order.index(word)] = -float(coefficient)
    identity_slot = order.index(identity)
    # The identity coefficient is the objective, not a constraint; every other group is pinned.
    weightings = np.ones(count)
    weightings[identity_slot] = 0.0
    objective_direction = np.zeros(count)
    objective_direction[identity_slot] = 1.0

    def value_and_gradient(flat, weight):
        factor = flat.reshape(size, size)
        matrix = factor.T @ factor
        sums = np.bincount(index, weights=matrix.ravel(), minlength=count)
        residual = (sums - target) * weightings
        value = sums[identity_slot] + weight * float(residual @ residual)
        coefficients = objective_direction + 2.0 * weight * residual * weightings
        outer = coefficients[index].reshape(size, size)
        gradient = factor @ (outer + outer.T)
        return value, gradient.ravel()

    best = None
    for attempt in range(restarts):
        rng = np.random.default_rng(seed + attempt)
        flat = rng.normal(scale=0.5, size=size * size)
        for weight in (1e2, 1e4, 1e6, 1e8, 1e10, 1e12):
            result = minimize(value_and_gradient, flat, args=(weight,), jac=True,
                              method="L-BFGS-B",
                              options={"maxiter": 20000, "maxfun": 40000,
                                       "ftol": 1e-18, "gtol": 1e-16})
            flat = result.x
        factor = flat.reshape(size, size)
        matrix = factor.T @ factor
        sums = np.bincount(index, weights=matrix.ravel(), minlength=count)
        violation = float(np.max(np.abs((sums - target) * weightings)))
        if violation < 1e-7 and (best is None or sums[identity_slot] < best[0]):
            best = (sums[identity_slot], matrix)
    if best is None:
        return None
    return best[1]


def rationalise(numeric, basis, groups, functional, denominator):
    """Round, repair the identity exactly, then shift the diagonal until PSD holds."""
    size = len(basis)
    identity = ((), ())
    matrix = [[Fraction(round(numeric[i, j] * denominator), denominator) for j in range(size)]
              for i in range(size)]
    for i in range(size):
        for j in range(i + 1, size):
            averaged = (matrix[i][j] + matrix[j][i]) / 2
            matrix[i][j] = matrix[j][i] = averaged
    # Exact repair of every constrained word. The identity group is the diagonal and is left
    # alone: its sum is the bound, which is the objective rather than a constraint.
    required = {word: Fraction(-coefficient) for word, coefficient in functional.items()}
    for word, cells in groups.items():
        if word == identity:
            continue
        have = sum(matrix[i][j] for i, j in cells)
        shift = (required.get(word, Fraction(0)) - have) / len(cells)
        if shift == 0:
            continue
        for i, j in cells:
            matrix[i][j] += shift
    # Symmetry survives the repair because the cell set of every word is closed under transpose:
    # if s^dagger t = w then t^dagger s = w^dagger, and the two groups get the same shift only
    # when w is self-adjoint. Re-symmetrise rather than assume it.
    for i in range(size):
        for j in range(i + 1, size):
            if matrix[i][j] != matrix[j][i]:
                averaged = (matrix[i][j] + matrix[j][i]) / 2
                matrix[i][j] = matrix[j][i] = averaged
    for word, cells in groups.items():
        if word == identity:
            continue
        have = sum(matrix[i][j] for i, j in cells)
        shift = (required.get(word, Fraction(0)) - have) / len(cells)
        if shift != 0:
            for i, j in cells:
                matrix[i][j] += shift
    def shifted_by(epsilon):
        return [[matrix[i][j] + (epsilon if i == j else 0) for j in range(size)]
                for i in range(size)]

    if is_positive_semidefinite(matrix, size):
        return matrix
    # Double until it holds, then bisect back down. Doubling alone can overpay by a factor of two,
    # and the diagonal shift is charged straight to the bound: |basis| * epsilon is added to the
    # identity coefficient, so on CHSH an overshoot of 4e-3 was most of the reference's distance
    # from Tsirelson's bound.
    high = Fraction(1, denominator)
    for _ in range(200):
        if is_positive_semidefinite(shifted_by(high), size):
            break
        high *= 2
    else:
        raise RuntimeError("could not restore positive semidefiniteness")
    low = Fraction(0)
    for _ in range(60):
        middle = (low + high) / 2
        if middle.denominator > 10 ** 12:
            break
        if is_positive_semidefinite(shifted_by(middle), size):
            high = middle
        else:
            low = middle
    return shifted_by(high)


def exact_ldl_squares(matrix, size):
    """Write a rational PSD matrix as an exact sum of weighted squares.

    Q = sum_k d_k w_k w_k^T with every d_k >= 0, by symmetric elimination. The elimination is done
    once here, where it is the reference's own cost, rather than in the oracle where an adversarial
    submission could make it unbounded. Raises if the matrix is not semidefinite.
    """
    work = [[Fraction(value) for value in row] for row in matrix]
    squares = []
    for k in range(size):
        pivot_row = max(range(k, size), key=lambda r: work[r][r])
        if work[pivot_row][pivot_row] < 0:
            raise ValueError("matrix is not positive semidefinite")
        if work[pivot_row][pivot_row] == 0:
            if any(work[r][c] != 0 for r in range(k, size) for c in range(k, size)):
                raise ValueError("matrix is not positive semidefinite")
            break
        # Pivoting would permute the basis; instead take the pivot in place when it is usable and
        # fall back to the largest only if the diagonal entry here has died.
        if work[k][k] == 0:
            work[k], work[pivot_row] = work[pivot_row], work[k]
            for r in range(size):
                work[r][k], work[r][pivot_row] = work[r][pivot_row], work[r][k]
        pivot = work[k][k]
        vector = [Fraction(0)] * size
        vector[k] = Fraction(1)
        for c in range(k + 1, size):
            vector[c] = work[k][c] / pivot
        # Clear denominators: write v = (g / L) * n with n an integer vector of content 1, and
        # move (g / L)^2 into the weight. Every product weight * v_i * v_j is unchanged. Without
        # this the LDL vectors carry ratios of leading minors and blow through the oracle's caps.
        multiplier = 1
        for entry in vector:
            multiplier = multiplier * entry.denominator // math.gcd(multiplier, entry.denominator)
        integral = [int(entry * multiplier) for entry in vector]
        content = 0
        for entry in integral:
            content = math.gcd(content, abs(entry))
        if content > 1:
            integral = [entry // content for entry in integral]
        scale = Fraction(content if content else 1, multiplier)
        squares.append((pivot * scale * scale, [Fraction(entry) for entry in integral]))
        for r in range(k + 1, size):
            factor = work[r][k]
            if factor == 0:
                continue
            factor = factor / pivot
            for c in range(k + 1, size):
                work[r][c] -= factor * work[k][c]
    return squares


def _rational(value):
    return [value.numerator, value.denominator]

def build_certificate(instance):
    basis = [((), ())] + [((i,), ()) for i in range(4)] + [((), (j,)) for j in range(4)]
    basis += [(tuple(a), tuple(b)) for a, b in instance["moment_pool"][:instance["extra_budget"]]]
    groups = word_groups(basis)
    numeric = _factored_solution(instance["functional"], basis, groups, restarts=1)
    if numeric is None:
        raise RuntimeError("numerical search did not produce a repairable identity")
    matrix = rationalise(numeric, basis, groups, instance["functional"], 10**7)
    squares = exact_ldl_squares(matrix, len(basis))
    return {"basis": [[list(a), list(b)] for a, b in basis],
            "squares": [{"weight": _rational(w), "vector": [_rational(x) for x in v]}
                        for w, v in squares]}
