#!/usr/bin/env bash
set -euo pipefail
echo "[entrypoint] Starting Gunicorn..."
exec gunicorn -w "${GUNICORN_WORKERS:-2}" -b 0.0.0.0:"${PORT:-8000}" app:app
