#!/usr/bin/env bash
# ==============================================================================
# Curriculum Gap Analysis Pipeline - One-Touch Startup Script
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================================================"
echo " Starting Curriculum Gap Analysis Pipeline (Multi-Agent System)"
echo "========================================================================"

# 1. Check Python Virtual Environment
if [ -d "venv" ]; then
    echo "[✓] Virtual environment detected: venv/"
    source venv/bin/activate
else
    echo "[!] Virtual environment not found. Creating venv..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# 2. Check Node & Frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "[!] Frontend dependencies not found. Installing..."
    (cd frontend && npm install)
fi

# Ensure frontend production build exists
if [ ! -d "frontend/dist" ]; then
    echo "[*] Building frontend assets..."
    (cd frontend && npm run build)
fi

echo ""
echo "========================================================================"
echo " ACCESS URLS:"
echo "   - Web Dashboard (UI):    http://localhost:5173"
echo "   - Backend REST API:     http://localhost:8000"
echo "   - Interactive Swagger:  http://localhost:8000/docs"
echo "========================================================================"
echo ""
echo "[*] Starting FastAPI Backend on port 8000 (with auto-reload)..."
./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[*] Starting Vite Frontend on port 5173..."
(cd frontend && npm run dev -- --host 0.0.0.0 --port 5173) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "[*] Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "[✓] Pipeline shut down safely."
    exit 0
}

trap cleanup INT TERM

wait
