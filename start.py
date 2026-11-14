#!/usr/bin/env python3
"""
start.py
========
Cross-platform launcher for both Backend (FastAPI) and Frontend (Vite).
Runs both processes concurrently and handles clean shutdown on Ctrl+C.

Usage:
  python start.py
  or
  ./venv/bin/python start.py
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 72)
    print(" Curriculum Gap Analysis Pipeline - Multi-Agent AI System")
    print("=" * 72)

    # Detect python executable in venv
    venv_py = ROOT_DIR / "venv" / "bin" / "python"
    if not venv_py.exists():
        venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe" # Windows fallback
    if not venv_py.exists():
        venv_py = Path(sys.executable)

    print(f"[*] Python runtime: {venv_py}")

    # Check frontend build / node_modules
    frontend_dir = ROOT_DIR / "frontend"
    if not (frontend_dir / "node_modules").exists():
        print("[!] Installing frontend packages...")
        subprocess.run(["npm", "install"], cwd=str(frontend_dir), check=True)

    print("\n" + "=" * 72)
    print(" WEB ACCESS URLS:")
    print("   👉 Web Dashboard (UI):    http://localhost:5173")
    print("   👉 Backend REST API:     http://localhost:8000")
    print("   👉 Swagger API Docs:     http://localhost:8000/docs")
    print("=" * 72 + "\n")

    # Start backend
    backend_proc = subprocess.Popen(
        [
            str(venv_py),
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        cwd=str(ROOT_DIR),
    )

    # Start frontend
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
        cwd=str(frontend_dir),
    )

    def shutdown(sig, frame):
        print("\n[*] Stopping servers...")
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
        except Exception:
            pass
        print("[✓] All processes stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[!] Backend exited unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[!] Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
