#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$REPO_ROOT/ui/resources/backend"
BUILD_DIR="$REPO_ROOT/.pyinstaller-build"

rm -rf "$BUILD_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

python3 -m venv "$BUILD_DIR/venv"

# shellcheck source=/dev/null
source "$BUILD_DIR/venv/bin/activate"

pip install --upgrade pip
pip install -r "$REPO_ROOT/requirements.txt" pyinstaller

pyinstaller \
  --name macputty-backend \
  --onedir \
  --noconfirm \
  --distpath "$OUT_DIR" \
  --workpath "$BUILD_DIR/work" \
  --specpath "$BUILD_DIR" \
  --add-data "$REPO_ROOT/config.conf:." \
  --add-data "$REPO_ROOT/ssh/ssh-connection-test.py:ssh" \
  --collect-all cryptography \
  --collect-all paramiko \
  --hidden-import nacl \
  --hidden-import bcrypt \
  --hidden-import pyparsing \
  "$REPO_ROOT/core/app.py"

deactivate
chmod +x "$OUT_DIR/macputty-backend/macputty-backend"
echo "Backend built at: $OUT_DIR/macputty-backend/macputty-backend"