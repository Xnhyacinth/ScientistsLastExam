"""Independent scalar geometric-tail checks for the documented compliance argument.

This is an oracle/math audit, not an audit(problem, sample) candidate. It imports no task
oracle, candidate implementation or private world. Its inputs must be supplied by the caller.
"""
import math


def dlap_tail(scale, threshold):
    """Infinite-support discrete Laplace P[X >= threshold], at an integer threshold."""
    ratio = math.exp(-1.0 / scale)
    if threshold > 0:
        return ratio ** threshold / (1.0 + ratio)
    return 1.0 - ratio ** (1 - threshold) / (1.0 + ratio)


def omitted_mass(scale, support):
    ratio = math.exp(-1.0 / scale)
    return 2.0 * ratio ** (support + 1) / (1.0 + ratio)


def dissent_upper_bound(threshold_scale, query_scale, offset, side, support=1200):
    """One comparison's dissent, with an analytic bound for omitted threshold noise.

    Query-noise tails use the infinite-support expression, not the oracle's truncated array.
    The 1e-12 slack is for floating-point numerical checking; it is not an interval-arithmetic
    certificate. The exact-real omitted-tail term is a rigorous upper bound.
    """
    ratio = math.exp(-1.0 / threshold_scale)
    normalizer = (1.0 - ratio) / (1.0 + ratio)
    terms = []
    for rho in range(-support, support + 1):
        if side == 'up':
            # nu < rho - offset, written without subtractive cancellation.
            dissent = dlap_tail(query_scale, offset - rho + 1)
        elif side == 'down':
            dissent = dlap_tail(query_scale, rho + offset)
        else:
            raise ValueError('side must be up or down')
        terms.append(normalizer * ratio ** abs(rho) * dissent)
    return math.fsum(terms) + omitted_mass(threshold_scale, support) + 1e-12


def coupling_delta_bound(threshold_scale, query_scale, offset, side, positions, cutoff, epsilon=1.0):
    dissent = dissent_upper_bound(threshold_scale, query_scale, offset, side)
    # For up/c=1, the first eligible position either causes the sole divergence or both
    # mechanisms emit T and halt. Otherwise a union bound covers all eligible positions.
    factor = 1 if side == 'up' and cutoff == 1 else positions
    return factor * dissent * (1.0 + math.exp(epsilon))


def distribution_truncation_bound(threshold_scale, query_scale, n_queries, support=1200):
    """Total-variation bound from independently conditioning every noise within support.

    This excludes floating-point arithmetic error; that is checked separately in controls.
    """
    return omitted_mass(threshold_scale, support) + n_queries * omitted_mass(query_scale, support)
