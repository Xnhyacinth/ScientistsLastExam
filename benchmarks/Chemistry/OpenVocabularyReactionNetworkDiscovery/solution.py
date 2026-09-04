"""Weak valid baseline for OpenVocabularyReactionNetworkDiscovery.

It makes no probes and declines every world.  The evaluator subtracts exactly
the unsupported-world credit earned by this policy, so its public score is 0.
"""
from __future__ import annotations


def discover_reaction_network(problem, probe):
    del problem, probe
    return {"abstain": True, "confidence": 0.0}
