# LyapunovDecayCertificate — scientific admission hold

## Reference

`verification/reference_lyapunov.py` uses only public modes. It retains the eight rational
Gram candidates but replaces the seven-rate table with exact rational bisection. The public
trace bound brackets feasible alpha and the public numerator/denominator cap sets precision.
The returned rate cannot be increased by 1e-4 while keeping the same Gram feasible.

Current in-process reference score: **0.8496395**, all four instances valid. Proven rates:
shear 119999/200000; pair 59961/100000; three 28553/47619; mid 199903/250000.
This fixes an incomplete reference search, not the scientific difficulty of the instance family.

## Baseline

The identity Gram at alpha=1/10000 is legal and scores exactly zero.

## Shortcut probes

`references/constant_probe.py` does no instance-dependent work and scores **0.786533**
on every instance. It exceeded the former coarse reference **0.7498665**. These two
numbers were independently reproduced in-process on September 9.

The [owner review](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/27#issuecomment-5594779605)
reports a 0.1-second coarse grid at 0.799867 and a 1.7-second grid plus rational bisection
at 0.849180. These timings are maintainer measurements. The repaired reference is itself
near the approximately 0.849900 mean ceiling, leaving no demonstrated frontier-search margin.
A larger rational catalog is therefore not established as meaningful long-horizon headroom.

## Construction errors

The former reference already had useful Gram matrices but suppressed its rate through a
coarse table. That omission is repaired without changing the score scale or reducing witness
capability. Baseline prose now says exactly zero; runtime timeout is explicitly declared.

## Robustness and required redesign

These are four fixed 2-by-2 rational systems. Floats and malformed certificates fail closed;
numerically found matrices converted to exact rational witnesses are not inherently forbidden.
A genuinely coupled higher-dimensional family and independent identity, single-mode,
averaged-mode and low-dimensional-grid probes are needed before a hardness claim. No padded
old instance or change of basis is claimed as that redesign. The PR remains Draft; no model
calibration or long-horizon evidence was created.
