#!/usr/bin/env bash
# Per-boot reconciliation for the MGT 409 environment.
#
# Environment builds do not re-run `install` on every boot, and the virtualenv
# lives under the git-managed /workspace tree, so a freshly booted pod may not
# have a .venv yet. Recreate it here when missing. This is fast (a no-op) once
# the venv exists, and it guarantees the `jupyter` terminal and `.venv` tooling
# are ready on every boot.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
  echo "No .venv found on boot; bootstrapping via install.sh..."
  bash .cursor/install.sh
else
  echo ".venv present; environment ready."
fi
