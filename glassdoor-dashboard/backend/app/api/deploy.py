"""Deploy control API – export static data and deploy to GitHub Pages."""

import os
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["deploy"])

PROJECT_ROOT = Path(__file__).resolve().parents[4]
FRONTEND_DIR = PROJECT_ROOT / "glassdoor-dashboard" / "frontend"
EXPORT_SCRIPT = PROJECT_ROOT / "export_static.py"

_export_state = {
    "running": False,
    "logs": [],
    "process": None,
    "success": None,  # True / False / None (not run yet)
}

_deploy_state = {
    "running": False,
    "logs": [],
    "process": None,
    "success": None,
}


def _read_output(proc: subprocess.Popen, state: dict):
    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            if line:
                state["logs"].append(line)
    except Exception:
        pass
    finally:
        rc = proc.wait()
        state["success"] = rc == 0
        state["running"] = False
        state["process"] = None


@router.post("/deploy/export")
def start_export():
    """Run export_static.py to generate static JSON data."""
    if _export_state["running"]:
        return {"error": "Export is already running"}
    if _deploy_state["running"]:
        return {"error": "Deploy is running; wait for it to finish first"}

    _export_state["logs"] = []
    _export_state["running"] = True
    _export_state["success"] = None

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, str(EXPORT_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT),
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    _export_state["process"] = proc
    threading.Thread(target=_read_output, args=(proc, _export_state), daemon=True).start()
    return {"status": "started"}


@router.post("/deploy/deploy")
def start_deploy():
    """Run npm run deploy in the frontend directory (build:static + gh-pages push)."""
    if _deploy_state["running"]:
        return {"error": "Deploy is already running"}
    if _export_state["running"]:
        return {"error": "Export is running; wait for it to finish first"}

    _deploy_state["logs"] = []
    _deploy_state["running"] = True
    _deploy_state["success"] = None

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    # Use cmd /c so npm (a .cmd script) works on Windows
    proc = subprocess.Popen(
        ["cmd", "/c", "npm", "run", "deploy"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(FRONTEND_DIR),
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    _deploy_state["process"] = proc
    threading.Thread(target=_read_output, args=(proc, _deploy_state), daemon=True).start()
    return {"status": "started"}


@router.get("/deploy/status")
def deploy_status():
    """Get status and logs for both export and deploy tasks."""
    return {
        "export": {
            "running": _export_state["running"],
            "logs": _export_state["logs"][-200:],
            "success": _export_state["success"],
        },
        "deploy": {
            "running": _deploy_state["running"],
            "logs": _deploy_state["logs"][-200:],
            "success": _deploy_state["success"],
        },
    }


@router.post("/deploy/stop")
def stop_deploy():
    """Stop any running export or deploy process."""
    stopped = []
    for name, state in [("export", _export_state), ("deploy", _deploy_state)]:
        proc = state.get("process")
        if proc and state["running"]:
            try:
                proc.kill()
            except Exception:
                pass
            state["running"] = False
            state["process"] = None
            state["logs"].append(f"[SYSTEM] {name} terminated by user")
            stopped.append(name)
    return {"stopped": stopped}
