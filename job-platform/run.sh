#!/usr/bin/env bash
# One-command local runner for CareerHound.
#
#   ./run.sh            # set up (if needed) + run backend :8000 and frontend :5173
#   ./run.sh backend    # backend only
#   ./run.sh frontend   # frontend only
#   ./run.sh single     # build UI + serve EVERYTHING from one URL (http://localhost:8000)
#   ./run.sh setup      # install deps only, don't run
#
# Requires: python3.10+, node 18+ (npm). Ctrl-C stops both servers.
set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

setup_backend() {
  echo "==> Backend: creating venv + installing deps"
  cd backend
  [ -d .venv ] || python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -q --upgrade pip
  pip install -q -r requirements.txt
  [ -f .env ] || cp .env.example .env
  cd ..
}

setup_frontend() {
  echo "==> Frontend: installing deps"
  cd frontend
  [ -d node_modules ] || npm install --no-fund --no-audit
  cd ..
}

run_backend() {
  cd backend
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "==> Backend on http://localhost:${BACKEND_PORT}  (docs: /docs)"
  exec uvicorn app.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}"
}

run_frontend() {
  cd frontend
  echo "==> Frontend on http://localhost:${FRONTEND_PORT}"
  exec npm run dev -- --port "${FRONTEND_PORT}"
}

case "${1:-all}" in
  setup)
    setup_backend; setup_frontend
    echo "Setup complete. Run ./run.sh to start."
    ;;
  backend)
    setup_backend; run_backend
    ;;
  frontend)
    setup_frontend; run_frontend
    ;;
  single)
    # Build the frontend once, then serve it + the API from the backend on one port.
    setup_frontend
    echo "==> Building frontend"
    ( cd frontend && npm run build )
    setup_backend
    run_backend
    ;;
  all)
    setup_backend; setup_frontend
    # Start backend in the background, frontend in the foreground.
    ( run_backend ) &
    BACK_PID=$!
    trap 'echo; echo "Stopping…"; kill $BACK_PID 2>/dev/null || true' EXIT INT TERM
    run_frontend
    ;;
  *)
    echo "Usage: ./run.sh [all|backend|frontend|setup]"; exit 1
    ;;
esac
