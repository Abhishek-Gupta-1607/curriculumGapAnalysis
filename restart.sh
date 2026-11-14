#!/usr/bin/env bash
# ==============================================================================
# Curriculum Gap Analysis Pipeline - Clean Restart Script
# ==============================================================================

echo "========================================================================"
echo " Restarting Curriculum Gap Analysis Pipeline"
echo "========================================================================"

echo "[*] Freeing ports 8000 and 5173..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
sleep 1

echo "[*] Rebuilding frontend assets..."
(cd frontend && npm run build)

echo "[*] Launching fresh servers..."
./start.sh
