#!/usr/bin/env bash
set -euo pipefail

# =====================================
# 기본 설정
# =====================================
ENTRYPOINT="app.py"
VENV_DIR=".venv"
PYTHON_BIN="python3"
SKIP_ESP32_CHECK="${SKIP_ESP32_CHECK:-0}"

# =====================================
# 경로 설정
# =====================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "[INFO] project dir: $PROJECT_DIR"

# =====================================
# 옵션 처리
# =====================================
if [[ "${1:-}" == "--skip-esp32" || "${1:-}" == "--no-esp32" ]]; then
  SKIP_ESP32_CHECK=1
  shift
fi

export SKIP_ESP32_CHECK

# =====================================
# venv 준비
# =====================================
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[INFO] venv not found → creating $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# =====================================
# pip 의존성 설치
# =====================================
if [[ -f "requirements.txt" ]]; then
  echo "[INFO] installing requirements.txt"
  pip install -r requirements.txt
else
  echo "[WARN] requirements.txt not found (skip)"
fi

# =====================================
# 실행
# =====================================
echo "[INFO] starting app: $ENTRYPOINT"
echo "[INFO] press Ctrl+C to stop"

exec "$VENV_DIR/bin/python" "$ENTRYPOINT"
