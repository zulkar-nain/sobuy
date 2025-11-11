#!/usr/bin/env bash
# Run this inside your virtualenv to pin requirements.txt
# Usage:
#   source venv/bin/activate
#   ./scripts/pin_requirements.sh

PYTHON=${PYTHON:-python}
ROOT_DIR="$(dirname "$0")/.."
REQ_FILE="$ROOT_DIR/requirements.txt"
BACKUP="$REQ_FILE.bak"

set -euo pipefail

echo "Using interpreter: $($PYTHON -c 'import sys; print(sys.executable)')"
$PYTHON -m pip freeze > "$REQ_FILE"
if [ -f "$REQ_FILE" ]; then
  echo "Pinned requirements written to $REQ_FILE"
fi

echo "Consider reviewing $REQ_FILE before committing."

echo "To commit: git add requirements.txt && git commit -m 'chore: pin requirements'" > /dev/stderr
