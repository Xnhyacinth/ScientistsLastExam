# ProcessMicrostructurePropertyDesign — design the processing schedule, not the microstructure

## Scientific question

Can a policy propose a *manufacturable processing archive* whose blend composition, anneal,
cooling and draw schedules improve a three-way Pareto frontier in specific modulus, transport
barrier and process energy, while transferring across sealed material and process-model shifts?

The output is a process recipe, not a microstructure image. The evaluator evolves the recipe
through a frozen reduced-order phase-field/coarsening model and then homogenizes its properties.
This is a deterministic synthetic mechanism benchmark. The reduced quantities are not validated
for any named commercial polymer or alloy. A high score is evidence only that a search policy
improved this frozen process--structure--property oracle, not that it discovered a real material.

## Relationship to neighbouring repository tasks

- `PhaseDiagramDiscovery` discovers equilibrium phase topology; here the unknown is a
  manufacturable processing archive and the order is process, microstructure, then property.
- `AlloyHardnessOptimization` chooses alloy candidates from a finite evidence table; here all five
  continuous process coordinates are constructed by the candidate.
- `ElectrolyteConductivityDesign` optimizes formulation-level conductivity evidence; this task
  jointly scores modulus, barrier transport and processing energy after simulated morphology.
- `MolecularLeadOptimization` searches molecular structures; this task holds constituent identity
  fixed and changes composition, thermal history, cooling and draw.
- `DistillationColumnDesign` optimizes separation equipment; this task models material
  microstructure formation and homogenized solid properties, not a process flowsheet.

## What to implement

```python
def design_process_archive(problem):
    ...
    return {"processes": [...]}
```

Return 4--20 processes that are distinct at the published manufacturing resolutions. Each
process must contain exactly:

```python
{
    "blend_fraction_b": 0.50,
    "anneal_temperature": 0.62,
    "anneal_time": 6.0,
    "cooling_rate": 0.8,
    "draw_ratio": 2.2,
}
```

All values are finite reduced process coordinates. They must obey the supplied `bounds`:

| process field | current bound | interpretation |
|---|---:|---|
| `blend_fraction_b` | `[0.15, 0.85]` | feed fraction of constituent B |
| `anneal_temperature` | `[0.45, 0.95]` | reduced annealing temperature |
| `anneal_time` | `[0.5, 12.0]` | reduced residence time |
| `cooling_rate` | `[0.20, 4.0]` | reduced controlled cooling rate |
| `draw_ratio` | `[1.0, 4.0]` | post-anneal uniaxial draw ratio |

An array, image, latent vector, target property, or predicted microstructure is not a process and
is rejected. Values are rounded to the nearest published manufacturing bin before evaluation;
two schedules in the same bin are duplicates and are rejected.

## Public problem mapping

Every key passed to `design_process_archive` is listed here:

| key | meaning |
|---|---|
| `process_fields` | ordered names `blend_fraction_b`, `anneal_temperature`, `anneal_time`, `cooling_rate`, `draw_ratio` |
| `bounds` | legal interval for every process coordinate |
| `archive_size_bounds` | minimum and maximum number of distinct schedules |
| `manufacturing_resolutions` | evaluator quantization step for every process coordinate |
| `grid_cells` | spatial cells in the frozen one-dimensional reduced model |
| `constituent_properties` | public nominal `reduced_modulus` and `reduced_permeability` pairs |
| `critical_temperature_estimate` | public nominal spinodal threshold estimate |
| `objective_normalization` | public offsets/scales for specific modulus and barrier index, and the process-energy maximum |
| `phase_field_model` | description of spectral conserved growth and coarsening closure |
| `homogenization_model` | description of the frozen Voigt--Reuss property closure |
| `objectives` | rows with objective `name` and optimization `sense` |
| `scope_warning` | explicit non-real-discovery interpretation |

The two nested inputs most easily confused with per-constituent records have these exact shapes.
The two entries in each property list are constituent A then B; they are not dictionaries:

```python
modulus_a, modulus_b = problem["constituent_properties"]["reduced_modulus"]
permeability_a, permeability_b = problem["constituent_properties"]["reduced_permeability"]

normalization = problem["objective_normalization"]
```

The mapping supplies constituent properties and score units, not a reference search recipe
or the hidden property-model coefficients.

## Frozen mechanism oracle

For each schedule, a deterministic initial composition perturbation is evolved in spectral space.
The linearized conserved phase-field term amplifies unstable wavelengths; a high-wave-number
penalty and cooling-dependent coarsening suppress fine structure; bounded nonlinear saturation
keeps the phase field physical and its mean composition is restored after clipping. The evaluator
does not expose or score an image.

The resulting local field enters a Voigt--Reuss interpolation. Crystallization is mobility-limited:
`Xc = Xeq * (1 - exp(-k * t_eff * exp(-Ec / (T + T0))))`, with world mobility multiplying `k`.
Crystallinity, interface density and draw modify reduced specific modulus and permeability.
The coefficients and worlds are benchmark-chosen, not literature-calibrated. This is a frozen mechanistic surrogate with declared shortcuts, not a neural surrogate
and not a first-principles prediction.

## Pareto scoring and continuing improvement

Each feasible process becomes one point with three maximize-oriented coordinates:

1. normalized `specific_modulus`;
2. normalized `barrier_index`;
3. energy saving derived from minimizing `process_energy`.

The evaluator computes exact three-dimensional hypervolume relative to the zero corner. Additional
non-dominated schedules can therefore add continuous marginal volume instead of only passing a
threshold. `combined_score` is development hypervolume normalized so the shipped conservative
four-process archive scores `0.0` and the independent public-problem-only 20-process witness scores
`1.0`. The release score is clipped to [0, 1]. Raw hypervolumes remain separate.

Reported separately are `development_hypervolume_score`,
`development_shifted_hypervolume_score`, feasibility, raw hypervolume, mean specific modulus,
mean barrier index, mean process energy and mean phase contrast. `heldout_hypervolume_score` and
`heldout_shifted_hypervolume_score` repeat the test on held-out materials. Each per-instance row
contains three `raw_shifted_hypervolumes`: reduced mobility/critical-temperature shift, stronger
gradient/interface penalty, and constituent-property shift. None of those sealed metrics enters
the public development score. `frontier_record_emitted` is true exactly when the evaluator emits
a transfer-eligible record and false otherwise; it does not assert that a ledger admitted the record.

A result emits a lifetime-credit frontier record only when the development score is at least 0.1, every held-out artifact is legal, and
the development-shifted, held-out, and held-out-shifted normalized scores each retain at least 50%
of the public development score. This frozen record-emission gate does not change `combined_score`; it
prevents a non-transferring archive from entering the cross-wave ledger.

## Rules and scientific scope

- Edit only `solution.py`; keep `design_process_archive(problem)`.
- Return only `{"processes": [...]}` with 4--20 manufacturing-distinct schedules inside all bounds.
- Use the supplied problem mapping; do not hard-code a material identity or access a split label.
- Deterministic CPU code only; standard library/NumPy/SciPy, no network or process creation.
- Do not read `verification/` or `frontier_eval/`.
- Real material claims require calibrated constituent data, higher-dimensional morphology,
  processing constraints, experimental manufacture, microscopy and independent property tests.

References: Cahn and Hilliard, *J. Chem. Phys.* (1958), conserved free-energy evolution, DOI
`10.1063/1.1744102`; Avrami, *J. Chem. Phys.* (1939), transformation kinetics, DOI
`10.1063/1.1750380`; Chen, *Annual Review of Materials Research* (2002), phase-field models, DOI
`10.1146/annurev.matsci.32.112001.132041`; Hill, *Proc. Phys. Soc. A* (1952), Voigt--Reuss
averaging, DOI `10.1088/0370-1298/65/5/307`; Nielsen, *J. Macromol. Sci. A* (1967), composite
permeability, DOI `10.1080/10601326708053745`; Ng et al., *Polymer* (2000), draw-dependent
polymer properties, DOI `10.1016/S0032-3861(99)00760-0`; Gutowski et al., *Environmental Science
& Technology* (2009), manufacturing energy, DOI `10.1021/es8016655`; Brough et al., *Integrating
Materials and Manufacturing Innovation* (2017), materials knowledge systems, DOI
`10.1007/s40192-017-0089-0`.
