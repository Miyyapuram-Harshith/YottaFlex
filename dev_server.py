#!/usr/bin/env python3
"""
ERL-RMA Unified Dev Server
Starts both the Python REST API server (port 8000) and the Vite frontend (port 5173)
in parallel, forwarding outputs and gracefully terminating both on SIGINT.
"""

import os
import signal
import subprocess
import sys
import time

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    print("\n=======================================================")
    print("  Starting YottaFlex ERL-RMA Unified Development Stack")
    print("=======================================================\n")

    # Start Backend API Server
    api_cmd = [sys.executable, "api_server.py", "--port", "8000"]
    print("-> [Backend] Launching REST API on http://localhost:8000 ...")
    api_proc = subprocess.Popen(api_cmd, cwd=root_dir)

    time.sleep(1.0)

    # Start Frontend Dev Server
    print("-> [Frontend] Launching Vite Dev Server on http://localhost:5173 ...")
    npm_bin = "npm"
    vite_cmd = [npm_bin, "run", "dev"]
    vite_proc = subprocess.Popen(vite_cmd, cwd=root_dir)

    def shutdown(sig, frame):
        print("\n\nShutting down ERL-RMA development stack...")
        for p in (vite_proc, api_proc):
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    while True:
        if api_proc.poll() is not None:
            print(f"[Backend] Process exited with code {api_proc.returncode}")
            shutdown(None, None)
        if vite_proc.poll() is not None:
            print(f"[Frontend] Process exited with code {vite_proc.returncode}")
            shutdown(None, None)
        time.sleep(0.5)

if __name__ == "__main__":
    main()

