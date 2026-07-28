#!/bin/bash

set -e

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON="$VENV_PATH/bin/python"
UVICORN="$VENV_PATH/bin/uvicorn"

echo "========================================"
echo "          OmniAgent Launcher"
echo "========================================"
echo ""

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run: uv sync"
    exit 1
fi

echo "[1/4] Cleaning up existing services..."
PORTS=(8000 5173)
for PORT in "${PORTS[@]}"; do
    PIDS=$(lsof -t -i:$PORT 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "      Port $PORT is occupied by PID(s) $PIDS, terminating..."
        for PID in $PIDS; do
            kill -9 $PID 2>/dev/null && echo "      ✅ Process $PID terminated" || echo "      ⚠️  Failed to terminate process $PID"
        done
    fi
done
sleep 1
echo "      ✅ Port cleanup completed"

echo ""
echo "[2/4] Activating virtual environment..."
$PYTHON --version

echo ""
echo "[3/4] Starting backend service..."
echo "      Backend: http://localhost:8000"
cd "$PROJECT_ROOT" && $UVICORN backend.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 3

echo ""
echo "[4/4] Starting frontend dev server..."
echo "      Frontend: http://localhost:5173"
cd "$PROJECT_ROOT/frontend" && npm run dev &
FRONTEND_PID=$!
sleep 3

echo ""
echo "========================================"
echo "          Services Started"
echo "========================================"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

wait