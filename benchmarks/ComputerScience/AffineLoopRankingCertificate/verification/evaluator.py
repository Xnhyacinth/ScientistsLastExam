"""Hidden oracle for AffineLoopRankingCertificate.

The product is a lexicographic tuple of linear ranking functions with Farkas
multipliers. A single linear ranking on the whole transition system is the
lattice this task leaves: these nested-reset loops are not 1-ranking complete.
"""
from __future__ import annotations

from fractions import Fraction

MAX_NUMERATOR = 10**18
MAX_DENOMINATOR = 10**18
MAX_COMPONENTS = 3
BASELINE_DELTA = Fraction(1, 10000)


def _ratio(numerator, denominator=1):
    if isinstance(numerator, Fraction):
        return [int(numerator.numerator), int(numerator.denominator)]
    return [int(numerator), int(denominator)]


def _fraction(value, name):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("%s must be an exact integer ratio, not a float" % name)
    if isinstance(value, int):
        result = Fraction(value, 1)
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        numerator, denominator = value
        if isinstance(numerator, bool) or isinstance(denominator, bool):
            raise ValueError("%s entries must be integers" % name)
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise ValueError("%s must be [numerator, denominator] integers" % name)
        if denominator == 0:
            raise ValueError("%s has a zero denominator" % name)
        result = Fraction(numerator, denominator)
    else:
        raise ValueError("%s is not an integer or [numerator, denominator] pair" % name)
    if abs(result.numerator) > MAX_NUMERATOR or abs(result.denominator) > MAX_DENOMINATOR:
        raise ValueError("%s exceeds the public magnitude cap" % name)
    return result


def _vector(raw, name, dimension):
    if not isinstance(raw, (list, tuple)) or len(raw) != dimension:
        raise ValueError("%s must be a length-%d vector" % (name, dimension))
    return [_fraction(item, "%s[%d]" % (name, index)) for index, item in enumerate(raw)]


def _matrix(raw, name, rows, cols):
    if not isinstance(raw, (list, tuple)) or len(raw) != rows:
        raise ValueError("%s must be a %dx%d matrix" % (name, rows, cols))
    return [_vector(row, "%s[%d]" % (name, index), cols) for index, row in enumerate(raw)]


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def _matvec_left(matrix, vector):
    """r |-> A^T r."""
    cols = len(matrix[0])
    return [
        sum(matrix[k][j] * vector[k] for k in range(len(vector)))
        for j in range(cols)
    ]


def _one_norm(vector):
    return sum(abs(item) for item in vector)


def _farkas(linear, constant, guards, lambdas):
    if len(lambdas) != len(guards):
        raise ValueError("lambda count must match the guard count")
    acc = [Fraction(0)] * len(linear)
    offset = Fraction(0)
    for lam, guard in zip(lambdas, guards):
        if lam < 0:
            return False
        slope, intercept = guard
        for index in range(len(linear)):
            acc[index] += lam * slope[index]
        offset += lam * intercept
    return acc == list(linear) and constant - offset >= 0


def _parse_guards(raw, dimension):
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("guards must be a nonempty list")
    parsed = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError("guards[%d] must be a mapping" % index)
        slope = _vector(item.get("g"), "guards[%d].g" % index, dimension)
        intercept = _fraction(item.get("d"), "guards[%d].d" % index)
        parsed.append((slope, intercept))
    return parsed


def _block_guards(width, skip):
    guards = []
    for index in range(width):
        slope = [_ratio(1 if j in (index, (index + 1) % width) else 0)
                 for j in range(width)]
        guards.append({"g": slope, "d": _ratio(-2)})
    for index in range(width):
        slope = [_ratio(2 if j == index else 1 if j == (index + skip) % width else 0)
                 for j in range(width)]
        guards.append({"g": slope, "d": _ratio(-3)})
    return guards


def _exit_guards(width):
    # v_i <= 1, so a reset that copies a large outer block increases any
    # positive inner ranking.
    return [{"g": [_ratio(-1 if j == index else 0) for j in range(width)],
             "d": _ratio(1)} for index in range(width)]


def _embed_guards(block_guards, offset, dimension):
    embedded = []
    for item in block_guards:
        slope = [_ratio(0)] * dimension
        block = item["g"]
        for index, value in enumerate(block):
            slope[offset + index] = value
        embedded.append({"g": slope, "d": item["d"]})
    return embedded


def _mixed_update(width):
    first = [_ratio(0)] * width
    first[0] = _ratio(1, 2)
    if width > 1:
        first[1] = _ratio(1, 8)
    if width > 2:
        first[2] = _ratio(-1, 4)
    if width > 3:
        first[3] = _ratio(1, 16)
    return [[first[(j - i) % width] for j in range(width)] for i in range(width)]


def _offset(width, well):
    return [_ratio(well if i == 0 else -(1 + i % 5)) for i in range(width)]


def _identity(width):
    return [[_ratio(int(i == j)) for j in range(width)] for i in range(width)]


def _zero_matrix(rows, cols):
    return [[_ratio(0)] * cols for _ in range(rows)]


def _zero_vector(width):
    return [_ratio(0)] * width


def _block_diag(blocks):
    dimension = sum(len(block) for block in blocks)
    matrix = _zero_matrix(dimension, dimension)
    offset = 0
    for block in blocks:
        width = len(block)
        for i in range(width):
            for j in range(width):
                matrix[offset + i][offset + j] = block[i][j]
        offset += width
    return matrix


def _place_block(matrix, row0, col0, block):
    for i, row in enumerate(block):
        for j, value in enumerate(row):
            matrix[row0 + i][col0 + j] = value


def _skip(width):
    return 1 if width < 4 else 3


def _level_spec(widths, wells):
    return list(zip(widths, wells, [_skip(width) for width in widths]))


def _concat(vectors):
    out = []
    for vector in vectors:
        out.extend(vector)
    return out


def _transition(name, guards, update_a, update_b):
    return {"name": name, "guards": guards, "A": update_a, "b": update_b}


def _nested_system(widths, wells):
    """Nested reset loops: inner progress, then reset the next block from the one that progressed.

    Transitions are innermost-first. A 1-ranking cannot serve both an inner progress
    step (needs a positive inner slope) and a reset (that slope increases).
    """
    levels = _level_spec(widths, wells)
    dimension = sum(widths)
    offsets = []
    cursor = 0
    for width, _, _ in levels:
        offsets.append(cursor)
        cursor += width
    identities = [_identity(width) for width, _, _ in levels]
    mixed = [_mixed_update(width) for width, _, _ in levels]
    large = [_embed_guards(_block_guards(width, skip), offset, dimension)
             for (width, _, skip), offset in zip(levels, offsets)]
    small = [_embed_guards(_exit_guards(width), offset, dimension)
             for (width, _, _), offset in zip(levels, offsets)]
    zeros = [_zero_vector(width) for width, _, _ in levels]
    offsets_b = [_offset(width, well) for width, well, _ in levels]
    transitions = []
    depth = len(levels)
    for stage in range(depth - 1, -1, -1):
        update_a = _block_diag(
            [identities[level] for level in range(depth)]
        )
        shift = list(zeros)
        guards = []
        for level in range(depth):
            if level < stage:
                guards.extend(large[level])
            elif level == stage:
                _place_block(update_a, offsets[level], offsets[level], mixed[level])
                shift[level] = offsets_b[level]
                guards.extend(large[level])
            elif level == stage + 1:
                row0 = offsets[level]
                col0 = offsets[stage]
                width = widths[level]
                for index in range(width):
                    for j in range(dimension):
                        update_a[row0 + index][j] = _ratio(0)
                    update_a[row0 + index][col0 + index] = _ratio(1)
                shift[level] = zeros[level]
                guards.extend(small[level])
            else:
                guards.extend(small[level])
        name = "inner" if stage == depth - 1 else ("outer" if stage == 0 else "mid_%d" % stage)
        transitions.append(_transition(name, guards, update_a, _concat(shift)))
    return dimension, transitions


def _nested_instance(name, widths, wells, score_one):
    dimension, transitions = _nested_system(widths, wells)
    return {
        "name": name,
        "dimension": dimension,
        "transitions": transitions,
        "score_one_quality": score_one,
        "n_levels": len(widths),
    }


# score_one_quality is the measured sum of component deltas of the evaluator-only
# constructive lex catalog, not a 1-ranking Farkas LP optimum. Filled after
# measurement; tests pin the catalog independently.
INSTANCES = (
    _nested_instance("reset_6", (3, 3), (-6, -9), [1037, 84]),
    _nested_instance("reset_8", (4, 4), (-8, -12), [3991, 248]),
    _nested_instance("nested_9", (3, 3, 3), (-5, -7, -9), [985, 56]),
    _nested_instance("nested_12", (4, 4, 4), (-6, -8, -12), [10821, 496]),
)


def public_instance(instance):
    return {
        "name": instance["name"],
        "dimension": instance["dimension"],
        "transitions": instance["transitions"],
        "max_numerator": MAX_NUMERATOR,
        "max_denominator": MAX_DENOMINATOR,
        "max_components": MAX_COMPONENTS,
    }


def _parse_transitions(raw, dimension):
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("transitions must be a nonempty list")
    parsed = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError("transitions[%d] must be a mapping" % index)
        guards = _parse_guards(item.get("guards"), dimension)
        update_a = _matrix(item.get("A"), "transitions[%d].A" % index, dimension, dimension)
        update_b = _vector(item.get("b"), "transitions[%d].b" % index, dimension)
        parsed.append((item.get("name") or "t%d" % index, guards, update_a, update_b))
    return parsed


def _validate(submission, dimension, n_transitions):
    if not isinstance(submission, dict):
        raise ValueError("submission must be a mapping")
    components = submission.get("components")
    if not isinstance(components, (list, tuple)) or not components:
        raise ValueError("components must be a nonempty list")
    if len(components) > MAX_COMPONENTS:
        raise ValueError("at most %d ranking components" % MAX_COMPONENTS)
    parsed = []
    for index, item in enumerate(components):
        if not isinstance(item, dict):
            raise ValueError("components[%d] must be a mapping" % index)
        ranking = _vector(item.get("r"), "components[%d].r" % index, dimension)
        if _one_norm(ranking) != 1:
            raise ValueError("components[%d].r must have exact 1-norm 1" % index)
        shift = _fraction(item.get("s"), "components[%d].s" % index)
        delta = _fraction(item.get("delta"), "components[%d].delta" % index)
        if delta <= 0:
            raise ValueError("components[%d].delta must be positive" % index)
        parsed.append((ranking, shift, delta))
    decrease_index = submission.get("decrease_index")
    if not isinstance(decrease_index, (list, tuple)) or len(decrease_index) != n_transitions:
        raise ValueError("decrease_index must have one entry per transition")
    indices = []
    for index, item in enumerate(decrease_index):
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError("decrease_index[%d] must be an integer" % index)
        if item < 0 or item >= len(parsed):
            raise ValueError("decrease_index[%d] is out of range" % index)
        indices.append(item)
    if set(indices) != set(range(len(parsed))):
        raise ValueError("every component must strictly decrease on at least one transition")
    nonneg = submission.get("nonneg_lambdas")
    decrease = submission.get("decrease_lambdas")
    if not isinstance(nonneg, (list, tuple)) or len(nonneg) != n_transitions:
        raise ValueError("nonneg_lambdas must have one block per transition")
    if not isinstance(decrease, (list, tuple)) or len(decrease) != n_transitions:
        raise ValueError("decrease_lambdas must have one block per transition")
    return parsed, indices, nonneg, decrease


def _component_lambdas(raw, name, n_components, n_guards, upto):
    if not isinstance(raw, (list, tuple)) or len(raw) != n_components:
        raise ValueError("%s must have one vector per component" % name)
    parsed = []
    for index, item in enumerate(raw):
        if index > upto:
            parsed.append(None)
            continue
        parsed.append(_vector(item, "%s[%d]" % (name, index), n_guards))
    return parsed


def certificate_holds(transitions, components, decrease_index, nonneg_raw, decrease_raw):
    for t_index, ((_, guards, update_a, update_b), active) in enumerate(
            zip(transitions, decrease_index)):
        n_guards = len(guards)
        n_components = len(components)
        try:
            nonneg = _component_lambdas(
                nonneg_raw[t_index], "nonneg_lambdas[%d]" % t_index, n_components, n_guards, active)
            decrease = _component_lambdas(
                decrease_raw[t_index], "decrease_lambdas[%d]" % t_index, n_components, n_guards, active)
        except ValueError as exc:
            return False, str(exc)
        for j in range(active + 1):
            ranking, shift, delta = components[j]
            if not _farkas(ranking, shift, guards, nonneg[j]):
                return False, "nonnegativity t%d c%d" % (t_index, j)
            linear_dec = [
                ranking[k] - _matvec_left(update_a, ranking)[k]
                for k in range(len(ranking))
            ]
            need = delta if j == active else Fraction(0)
            constant_dec = -_dot(ranking, update_b) - need
            if not _farkas(linear_dec, constant_dec, guards, decrease[j]):
                return False, "decrease t%d c%d" % (t_index, j)
    return True, None


def quality(components, decrease_index):
    used = set(decrease_index)
    return sum(components[index][2] for index in sorted(used))


def _score_instance(build, instance):
    published = {
        "name": instance["name"],
        "valid": False,
        "proven_quality": None,
        "instance_score": 0.0,
    }
    try:
        dimension = int(instance["dimension"])
        transitions = _parse_transitions(instance["transitions"], dimension)
        components, decrease_index, nonneg, decrease = _validate(
            build(public_instance(instance)), dimension, len(transitions)
        )
        holds, reason = certificate_holds(
            transitions, components, decrease_index, nonneg, decrease
        )
        if not holds:
            raise ValueError("lex Farkas certificate fails on %s" % reason)
        proven = quality(components, decrease_index)
        zero = BASELINE_DELTA * instance["n_levels"]
        ceiling = _fraction(instance["score_one_quality"], "score_one_quality")
        score = min(max(0.0, float((proven - zero) / (ceiling - zero))), 1.0)
        published.update({
            "valid": True,
            "proven_quality": [proven.numerator, proven.denominator],
            "instance_score": round(score, 6),
        })
    except Exception as exc:  # noqa: BLE001
        published["reason"] = "%s: %s" % (type(exc).__name__, exc)
    return published


def evaluate(build_ranking):
    rows = [_score_instance(build_ranking, instance) for instance in INSTANCES]
    valid = [row for row in rows if row["valid"]]
    combined = sum(row["instance_score"] for row in rows) / len(rows)
    return {
        "combined_score": float(round(combined, 6)),
        "valid": 1.0 if len(valid) == len(rows) else 0.0,
        "feasibility_rate": len(valid) / len(rows),
        "raw_score": float(round(combined, 6)),
        "instances_with_a_valid_certificate": len(valid),
        "per_instance": rows,
    }
