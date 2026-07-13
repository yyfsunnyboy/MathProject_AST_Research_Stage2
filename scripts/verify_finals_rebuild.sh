#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: verify_finals_rebuild.sh {targeted|related|full}" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

mode="$1"
case "$mode" in
  targeted|related|full) ;;
  *) usage; exit 2 ;;
esac

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: python is not available on PATH." >&2
  exit 2
fi
if ! python -m pytest --version; then
  echo "ERROR: pytest is unavailable for the active Python environment." >&2
  exit 2
fi

echo "Verification mode: $mode"
echo "Repository root: $REPO_ROOT"
echo "Git branch: $(git branch --show-current)"
echo "HEAD commit: $(git log -1 --oneline)"
echo "Python executable: $(command -v python)"
echo "Python version: $(python --version)"

if [[ -n "$(git status --short)" ]]; then
  echo "WARNING: working tree is dirty; verification will not modify it." >&2
fi

case "$mode" in
  targeted)
    python -m pytest -q \
      tests/finals_rebuild/test_math_dev_replay.py \
      tests/finals_rebuild/test_spec_adapter.py \
      tests/finals_rebuild/test_math_spec_rules.py
    ;;
  related)
    python -m pytest -q \
      tests/finals_rebuild/test_math_dev_replay.py \
      tests/finals_rebuild/test_spec_adapter.py \
      tests/finals_rebuild/test_math_spec_rules.py \
      tests/finals_rebuild/test_math_validator.py \
      tests/finals_rebuild/test_math_evaluator.py \
      tests/finals_rebuild/test_generator_evaluator.py \
      tests/finals_rebuild/test_generator_integration_pilot.py \
      tests/finals_rebuild/test_generator_healer_pilot.py
    ;;
  full)
    python -m pytest -q tests/finals_rebuild
    ;;
esac

git status --short
git diff --check
echo "VERIFICATION PASSED: $mode"
