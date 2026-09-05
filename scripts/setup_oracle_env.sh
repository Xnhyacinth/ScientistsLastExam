#!/usr/bin/env bash
# Install the domain toolkits the oracles need, on a host whose system pip is broken.
#
# Why this exists. Each task declares its oracle dependencies in verification/requirements.txt,
# and on the benchmark host `pip install -r` against those files does not work: the system
# interpreter's pip fails at import with
#
#     AttributeError: module 'lib' has no attribute 'X509_V_FLAG_NOTIFY_POLICY'
#
# which is a pyOpenSSL/cryptography binding mismatch in the distribution packages. A virtualenv
# created without --system-site-packages does not inherit the broken bindings, so its pip works;
# pointing that pip at the oracle interpreter's site-packages with --target installs where the
# oracle will actually look.
#
# The oracle runs in the trusted parent, not the sandbox, so installing here does not change the
# isolation model. Candidates receive a toolkit only if their task lists it in
# frontier_eval/candidate_packages.txt and the name appears in the audited allowlist in
# sle/secure_eval.py.
#
# Usage:
#     bash scripts/setup_oracle_env.sh            # install everything
#     bash scripts/setup_oracle_env.sh --check    # report what is present, install nothing
set -euo pipefail

ORACLE_PYTHON="${ORACLE_PYTHON:-/usr/bin/python3}"
BOOTSTRAP_VENV="${BOOTSTRAP_VENV:-$HOME/.cache/sle-bootstrap-venv}"

# Pinned to match the versions every reference record was measured against. Changing one of these
# invalidates that task's recorded anchors, which is why they are pinned rather than floated.
PACKAGES=(
  "stim==1.13.0"          # QuantumErrorDecoder: seeded sampling is not stable across versions
  "pymatching==2.4.0"     # QuantumErrorDecoder anchor
  "rdkit==2024.03.5"      # MolecularLeadOptimization; last line with cp38 wheels
  "ViennaRNA==2.7.2"      # RNAEnsembleDesign
  "nmrsim==0.6.0"         # SpinSystemInference
  "networkx==3.1"         # GraphFromDistances
  "sympy==1.13.3"         # SequenceLawRecovery
  "qutip==4.7.6"          # physics discovery tasks; 5.x needs a toolchain this host lacks
  "astropy==5.2.2"        # RadialVelocityPlanets Lomb--Scargle scoring platform
)

# import name -> pip name, since several differ
declare -A IMPORT_NAME=(
  ["stim==1.13.0"]="stim"
  ["pymatching==2.4.0"]="pymatching"
  ["rdkit==2024.03.5"]="rdkit"
  ["ViennaRNA==2.7.2"]="RNA"
  ["nmrsim==0.6.0"]="nmrsim"
  ["networkx==3.1"]="networkx"
  ["sympy==1.13.3"]="sympy"
  ["qutip==4.7.6"]="qutip"
  ["astropy==5.2.2"]="astropy"
)

# Canonical distribution versions. RDKit's import version retains a leading zero,
# while its distribution metadata uses the normalized spelling below.
declare -A EXPECTED_VERSION=(
  ["stim==1.13.0"]="1.13.0"
  ["pymatching==2.4.0"]="2.4.0"
  ["rdkit==2024.03.5"]="2024.3.5"
  ["ViennaRNA==2.7.2"]="2.7.2"
  ["nmrsim==0.6.0"]="0.6.0"
  ["networkx==3.1"]="3.1"
  ["sympy==1.13.3"]="1.13.3"
  ["qutip==4.7.6"]="4.7.6"
  ["astropy==5.2.2"]="5.2.2"
)

declare -A DISTRIBUTION_NAME=(
  ["stim==1.13.0"]="stim"
  ["pymatching==2.4.0"]="pymatching"
  ["rdkit==2024.03.5"]="rdkit"
  ["ViennaRNA==2.7.2"]="ViennaRNA"
  ["nmrsim==0.6.0"]="nmrsim"
  ["networkx==3.1"]="networkx"
  ["sympy==1.13.3"]="sympy"
  ["qutip==4.7.6"]="qutip"
  ["astropy==5.2.2"]="astropy"
)

site_dir() {
  # A configured virtualenv must own its packages; its user site is disabled and installing
  # there creates a plausible-looking environment that the interpreter never imports.
  # Preserve the historical user-site target only for a system interpreter.
  "$ORACLE_PYTHON" -c \
    "import site, sys, sysconfig; print(sysconfig.get_path('purelib') if sys.prefix != sys.base_prefix else site.getusersitepackages())"
}

installed_version() {
  local distribution="$1"
  "$ORACLE_PYTHON" -c \
    "import importlib.metadata, sys; print(importlib.metadata.version(sys.argv[1]))" \
    "$distribution" 2>/dev/null
}

package_matches() {
  local spec="$1"
  local mod="${IMPORT_NAME[$spec]}"
  local actual
  "$ORACLE_PYTHON" -c "import $mod" >/dev/null 2>&1 || return 1
  actual="$(installed_version "${DISTRIBUTION_NAME[$spec]}")" || return 1
  [[ "$actual" == "${EXPECTED_VERSION[$spec]}" ]]
}

report() {
  echo "oracle interpreter: $ORACLE_PYTHON ($("$ORACLE_PYTHON" -V 2>&1))"
  echo "target site-packages: $(site_dir)"
  local missing=0
  for spec in "${PACKAGES[@]}"; do
    local mod="${IMPORT_NAME[$spec]}"
    local version
    version="$(installed_version "${DISTRIBUTION_NAME[$spec]}")" 2>/dev/null || true
    if package_matches "$spec"; then
      printf '  %-22s present  %s\n' "$mod" "$version"
    elif [[ -n "$version" ]]; then
      printf '  %-22s MISMATCH %s (expected %s)\n' \
        "$mod" "$version" "${EXPECTED_VERSION[$spec]}"
      missing=$((missing + 1))
    else
      printf '  %-22s MISSING  (%s)\n' "$mod" "$spec"
      missing=$((missing + 1))
    fi
  done
  return "$missing"
}

if [[ "${1:-}" == "--check" ]]; then
  report || true
  exit 0
fi

if ! "$BOOTSTRAP_VENV/bin/python" -m pip --version >/dev/null 2>&1; then
  echo "creating bootstrap venv at $BOOTSTRAP_VENV"
  # No --system-site-packages: inheriting them is what pulls in the broken OpenSSL bindings.
  rm -rf "$BOOTSTRAP_VENV"
  "$ORACLE_PYTHON" -m venv "$BOOTSTRAP_VENV"
fi

TARGET="$(site_dir)"
echo "installing into $TARGET"
for spec in "${PACKAGES[@]}"; do
  mod="${IMPORT_NAME[$spec]}"
  if package_matches "$spec"; then
    echo "  $mod ${EXPECTED_VERSION[$spec]} already present, skipping"
    continue
  fi
  echo "  installing $spec"
  "$BOOTSTRAP_VENV/bin/pip" install --quiet --upgrade --target "$TARGET" "$spec"
done

echo
report
