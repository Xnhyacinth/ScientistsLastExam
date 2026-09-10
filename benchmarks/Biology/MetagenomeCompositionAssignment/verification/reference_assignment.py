"""Input-only conditional-likelihood reference with design and sparse refitting."""
from itertools import combinations, combinations_with_replacement
import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2
from scipy.special import ndtr


def _blocks(problem):
    matrix = np.asarray(problem["reference_profiles"], dtype=float)
    index = {name: i for i, name in enumerate(problem["marker_ids"])}
    indices = {int(panel): [index[name] for name in markers]
               for panel, markers in problem["panel_markers"].items()}
    return matrix, indices


def _fit(matrix, indices, observations):
    scale = sum(observation["read_count"] for observation in observations)
    def objective(weights):
        value = 0.
        gradient = np.zeros(len(weights))
        for observation in observations:
            selected = indices[observation["panel_id"]]
            block = matrix[selected]
            counts = np.asarray(observation["marker_counts"], dtype=float)[selected]
            mean = np.maximum(block @ weights, 1e-16)
            total, reads = mean.sum(), observation["read_count"]
            value += reads*np.log(total) - counts @ np.log(mean)
            gradient += reads*block.sum(axis=0)/total - block.T @ (counts/mean)
        return value/scale, gradient/scale
    result = minimize(objective, np.full(matrix.shape[1], 1/matrix.shape[1]), jac=True,
                      method="SLSQP", bounds=[(0., 1.)]*matrix.shape[1],
                      constraints={"type": "eq", "fun": lambda w: w.sum()-1,
                                   "jac": lambda w: np.ones(len(w))},
                      options={"maxiter": 1000, "ftol": 1e-12})
    if not result.success:
        raise RuntimeError("conditional likelihood did not converge: " + result.message)
    deviance = 0.
    for observation in observations:
        selected = indices[observation["panel_id"]]
        mean = matrix[selected] @ result.x
        expected = observation["read_count"]*mean/mean.sum()
        counts = np.asarray(observation["marker_counts"], dtype=float)[selected]
        positive = counts > 0
        deviance += 2*np.sum(counts[positive]*np.log(counts[positive]/expected[positive]))
    return result.x, float(deviance)


def _information(matrix, selected, weights, reads):
    block = matrix[selected]
    mean = block @ weights
    total = mean.sum()
    delta = block[:, :-1] - block[:, [-1]]
    derivative = (delta*total - mean[:, None]*delta.sum(axis=0))/total**2
    return reads*(derivative.T/(mean/total)) @ derivative


def _groups(problem, matrix, indices, observations):
    n = matrix.shape[1]
    distances = np.zeros((n, n))
    for observation in observations:
        block = matrix[indices[observation["panel_id"]]]
        roots = np.sqrt(block/block.sum(axis=0))
        difference = roots[:, :, None] - roots[:, None, :]
        distances += observation["read_count"]*problem["minimum_reported_abundance"]*np.sum(difference*difference, axis=0)
    connected = distances < problem["resolution_threshold"]
    unseen = set(range(n))
    groups = []
    while unseen:
        start = min(unseen)
        stack, group = [start], set()
        while stack:
            node = stack.pop()
            if node in group:
                continue
            group.add(node)
            stack.extend(int(i) for i in np.flatnonzero(connected[node]) if i not in group)
        unseen -= group
        groups.append(sorted(group))
    return groups


def _finish(problem, matrix, indices, observations, sparse_refit=True, adequacy_check=True):
    weights, deviance = _fit(matrix, indices, observations)
    degrees = sum(len(indices[o["panel_id"]])-1 for o in observations)
    # Conservatively retain all multinomial degrees of freedom rather than
    # treating boundary mixture coefficients as regular fitted parameters.
    if adequacy_check and deviance > chi2.ppf(.999, degrees):
        return dict(taxa=[], ambiguous_groups=[], abstain=True)
    groups = _groups(problem, matrix, indices, observations)
    selected = sorted(i for group in groups if sum(weights[j] for j in group) >= problem["minimum_reported_abundance"] for i in group)
    if sparse_refit and selected:
        fitted, _ = _fit(matrix[:, selected], indices, observations)
        weights = np.zeros(matrix.shape[1])
        weights[selected] = fitted
    taxa, aliases = [], []
    for group in groups:
        abundance = float(sum(weights[i] for i in group))
        if abundance < problem["minimum_reported_abundance"]:
            continue
        names = [problem["taxon_ids"][i] for i in group]
        if len(names) == 1:
            taxa.append(dict(taxon=names[0], abundance=abundance))
        else:
            aliases.append(dict(taxa=names, abundance=abundance))
    return dict(taxa=taxa, ambiguous_groups=aliases, abstain=False)


def _round_mass(output, bins):
    """Round and renormalize a complete assignment to preserve total mass.

    Reporting precision is calibrated on development worlds, not a claim
    about sequencing precision. A partial assignment is left untouched.
    """
    claims = output["taxa"] + output["ambiguous_groups"]
    mass = np.array([row["abundance"] for row in claims])
    if bins is None or not claims or abs(mass.sum()-1) > 1e-6:
        return output
    scaled = mass/mass.sum()*bins
    rounded = np.rint(scaled)/bins
    total = rounded.sum()
    if total:
        for row, value in zip(claims, rounded):
            row["abundance"] = float(value/total)
    return output


def _expected_credit(problem, matrix, indices, observations, weights, panel):
    """Local normal approximation to the public abundance/resolution utility."""
    future = observations + [dict(panel_id=panel, read_count=problem["reads_per_panel"])]
    groups = _groups(problem, matrix, indices, future)
    groups = [g for g in groups if sum(weights[i] for i in g) > .04]
    if len(groups) < 2:
        return -1e9
    mass = np.array([sum(weights[i] for i in g) for g in groups])
    mass /= mass.sum()
    collapsed = np.column_stack([np.average(matrix[:, g], axis=1, weights=weights[g]+1e-6) for g in groups])
    fisher = sum(_information(collapsed, indices[o["panel_id"]], mass, o["read_count"]) for o in future)
    covariance = np.linalg.inv(fisher + np.eye(len(groups)-1)*.001)
    variance = np.r_[np.diag(covariance), covariance.sum()]
    distances = {}
    for key, selected in indices.items():
        block = matrix[selected]
        roots = np.sqrt(block/block.sum(axis=0))
        distances[key] = problem["reads_per_panel"]*problem["minimum_reported_abundance"]*np.sum((roots[:, :, None]-roots[:, None, :])**2, axis=0)
    initial = problem["initial_observation"]["panel_id"]
    best = distances[initial]+2*np.maximum.reduce([distances[i] for i in problem["available_panels"]])
    reward = np.array([1. if len(g) == 1 or np.max(best[np.ix_(g, g)]) < problem["resolution_threshold"] else .5 for g in groups])
    sd = np.sqrt(np.maximum(variance, 1e-20))
    ratio = problem["abundance_tolerance"]/sd
    expected = 2*ndtr(ratio)-1-2*sd/problem["abundance_tolerance"]/np.sqrt(2*np.pi)*(1-np.exp(-ratio**2/2))
    return float(np.sum(mass*reward*(.2+.8*expected)))


def infer(problem, sequence, plan=None, sparse_refit=True, adequacy_check=True,
          adaptive=True, precision_bins=100):
    matrix, indices = _blocks(problem)
    observations = [problem["initial_observation"]]
    if plan is not None:
        observations.extend(sequence(panel) for panel in plan)
    else:
        pilot, _ = _fit(matrix, indices, observations)
        fisher = {panel: _information(matrix, selected, pilot, problem["reads_per_panel"])
                  for panel, selected in indices.items()}
        initial = problem["initial_observation"]["panel_id"]
        def design(panels):
            total = fisher[initial].copy()
            for panel in panels:
                total += fisher[panel]
            return np.linalg.slogdet(total + np.eye(matrix.shape[1]-1)*.001)[1]
        if adaptive:
            options = combinations_with_replacement(problem["available_panels"], problem["panel_budget"])
            first = max(options, key=design)[0]
            observations.append(sequence(first))
            updated, _ = _fit(matrix, indices, observations)
            second = max(problem["available_panels"], key=lambda panel: _expected_credit(problem, matrix, indices, observations, updated, panel))
            observations.append(sequence(second))
        else:
            options = combinations_with_replacement(problem["available_panels"], problem["panel_budget"])
            observations.extend(sequence(panel) for panel in max(options, key=design))
    output = _finish(problem, matrix, indices, observations, sparse_refit, adequacy_check)
    return _round_mass(output, precision_bins)



def _support_models(problem, matrix, indices, observations):
    """Approximate BIC weights over sparse reporting-unit supports, not a posterior.

    Near-alias columns are averaged while unresolved. Boundary fits retain the
    nominal parameter penalty; these weights are a planning approximation.
    """
    groups = _groups(problem, matrix, indices, observations)
    collapsed = np.column_stack([matrix[:, group].mean(axis=1) for group in groups])
    reads = sum(row["read_count"] for row in observations)
    models = []
    for size in range(1, min(4, len(groups))+1):
        for support in combinations(range(len(groups)), size):
            fitted, deviance = _fit(collapsed[:, support], indices, observations)
            bic = deviance + (size-1)*np.log(reads)
            weights = np.zeros(matrix.shape[1])
            for component, abundance in zip(support, fitted):
                group = groups[component]
                weights[group] = abundance/len(group)
            models.append((bic, weights))
    models.sort(key=lambda row: row[0])
    models = [row for row in models[:24] if row[0] <= models[0][0]+16]
    probabilities = np.exp(-.5*(np.array([row[0] for row in models])-models[0][0]))
    probabilities /= probabilities.sum()
    mean = np.sum([probability*weights for probability, (_, weights)
                   in zip(probabilities, models)], axis=0)
    return models, probabilities, mean


def sparse_design(problem, sequence, plan=None, adaptive=True,
                  adequacy_check=True, model_average=False):
    """Sparse support inference and two-stage abundance/resolution design."""
    matrix, indices = _blocks(problem)
    observations = [problem["initial_observation"]]
    if plan is not None:
        observations.extend(sequence(panel) for panel in plan)
    else:
        models, probabilities, weights = _support_models(problem, matrix, indices, observations)
        if not model_average:
            weights = models[0][1]
        options = combinations_with_replacement(problem["available_panels"], 2)
        def quality(pair):
            future = observations + [dict(panel_id=pair[0], read_count=problem["reads_per_panel"])]
            return _expected_credit(problem, matrix, indices, future, weights, pair[1])
        pair = max(options, key=quality)
        def discrimination(panel):
            means = np.array([matrix[indices[panel]] @ row[1] for row in models])
            means /= means.sum(axis=1, keepdims=True)
            average = probabilities @ means
            return float(np.sum(probabilities[:, None]*means*np.log(means/average)))
        first = max(pair, key=discrimination)
        observations.append(sequence(first))
        if adaptive:
            models, _, weights = _support_models(problem, matrix, indices, observations)
            if not model_average:
                weights = models[0][1]
            second = max(problem["available_panels"], key=lambda panel:
                         _expected_credit(problem, matrix, indices, observations, weights, panel))
        else:
            second = pair[1] if first == pair[0] else pair[0]
        observations.append(sequence(second))
    _, deviance = _fit(matrix, indices, observations)
    degrees = sum(len(indices[row["panel_id"]])-1 for row in observations)
    if adequacy_check and deviance > chi2.ppf(.999, degrees):
        return dict(taxa=[], ambiguous_groups=[], abstain=True)
    models, _, _ = _support_models(problem, matrix, indices, observations)
    weights = models[0][1]
    output = dict(taxa=[], ambiguous_groups=[], abstain=False)
    for group in _groups(problem, matrix, indices, observations):
        mass = float(weights[group].sum())
        if mass < problem["minimum_reported_abundance"]:
            continue
        names = [problem["taxon_ids"][i] for i in group]
        if len(group) == 1:
            output["taxa"].append(dict(taxon=names[0], abundance=mass))
        else:
            output["ambiguous_groups"].append(dict(taxa=names, abundance=mass))
    return output


def assign_composition(problem, sequence):
    return _round_mass(sparse_design(problem, sequence), 500)
