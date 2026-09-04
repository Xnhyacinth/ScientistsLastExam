"""Executable public-model witness; it is not asserted to be globally optimal."""
from __future__ import annotations


def design_finite_volume_method(problem):
    return {
        "reconstruction": "muscl",
        "limiter": "mc",
        "riemann_solver": "godunov",
        "time_integrator": "ssprk2",
        "cells": 96,
        "cfl": 0.72,
        "sensor_threshold": 0.28,
        "shock_blend": 0.82,
        "flux_dissipation": 1.0,
    }
