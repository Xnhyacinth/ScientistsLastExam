"""Canonical package pins shared by candidate isolation and oracle setup."""

from __future__ import annotations

from typing import Iterable


# Packages installed for trusted oracles. Candidate visibility remains separately allowlisted in
# secure_eval.py; this map only owns the versions used by both setup and runtime validation.
ORACLE_PACKAGE_PINS = {
    "stim": "1.13.0",
    "pymatching": "2.4.0",
    "rdkit": "2024.3.5",
    "ViennaRNA": "2.7.2",
    "nmrsim": "0.6.0",
    "networkx": "3.1",
    "sympy": "1.13.3",
    "qutip": "4.7.6",
    "astropy": "5.2.2",
}

# NumPy and SciPy are exposed to every candidate. The Python 3.8--3.11 line preserves the
# versions used for the recorded oracle anchors; Python 3.12 uses its repository-supported pair.
BASE_CANDIDATE_PINS = {
    (3, 8): {"numpy": "1.24.4", "scipy": "1.10.1"},
    (3, 9): {"numpy": "1.24.4", "scipy": "1.10.1"},
    (3, 10): {"numpy": "1.24.4", "scipy": "1.10.1"},
    (3, 11): {"numpy": "1.24.4", "scipy": "1.10.1"},
    (3, 12): {"numpy": "1.26.4", "scipy": "1.14.1"},
}

# These distributions carry Astropy's numerical and serialization behavior into Radial. They are
# mounted under their import-directory aliases, so validating only `astropy` is not sufficient.
TOOLKIT_DEPENDENCY_PINS = {
    "astropy": {"pyerfa": "2.0.0.3", "PyYAML": "6.0.2"},
}


def candidate_distribution_pins(
    python_version: tuple[int, int], toolkits: Iterable[str] = ()
) -> dict[str, str]:
    """Return the exact distributions that a candidate runtime must validate."""
    try:
        pins = dict(BASE_CANDIDATE_PINS[tuple(python_version)])
    except KeyError as exc:
        raise RuntimeError(
            "candidate package pins do not support Python %d.%d" % tuple(python_version)
        ) from exc
    for toolkit in toolkits:
        pins[toolkit] = ORACLE_PACKAGE_PINS[toolkit]
        pins.update(TOOLKIT_DEPENDENCY_PINS.get(toolkit, {}))
    return pins


def setup_requirements(python_version: tuple[int, int]) -> tuple[str, ...]:
    """Return one fully pinned transaction for scripts/setup_oracle_env.sh."""
    pins = dict(ORACLE_PACKAGE_PINS)
    pins.update(candidate_distribution_pins(python_version, ORACLE_PACKAGE_PINS))
    return tuple("%s==%s" % item for item in pins.items())
