#!/bin/sh
# Install the grounding plugin into a manual (PeTTa-based) Omega checkout.
#
#   sh plugin/install.sh /path/to/PeTTa/repos/Omega [/path/to/PeTTa/.venv]
#
# 1. installs the omega_grounding package into Omega's Python environment
# 2. links plugin/grounding into Omega/plugins/grounding
# 3. registers the plugin in Omega/config/plugins.yaml (once)
set -eu

OMEGA_DIR=${1:?usage: install.sh OMEGA_DIR [VENV_DIR]}
VENV_DIR=${2:-}
HERE=$(cd "$(dirname "$0")/.." && pwd)

if [ ! -f "$OMEGA_DIR/lib_omega.metta" ]; then
    echo "error: $OMEGA_DIR does not look like an Omega checkout" >&2
    exit 1
fi

PIP=pip3
if [ -n "$VENV_DIR" ]; then
    PIP="$VENV_DIR/bin/pip"
fi
"$PIP" install -e "$HERE"

ln -sfn "$HERE/plugin/grounding" "$OMEGA_DIR/plugins/grounding"

if ! grep -q "name: grounding" "$OMEGA_DIR/config/plugins.yaml"; then
    cat >> "$OMEGA_DIR/config/plugins.yaml" <<'EOF'

- name: grounding
  loader: metta
  location: "{REPO}/plugins/grounding"
EOF
fi

echo "Grounding plugin installed. Disable with OMEGA_groundingEnabled=disabled."
