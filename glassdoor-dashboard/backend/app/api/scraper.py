"""Scraper control API – launch, monitor, and check login status."""

import asyncio
import os
import subprocess
import sys
import time
import socket
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

router = APIRouter(tags=["scraper"])

# State
_scraper_state = {
    "running": False,
    "logs": [],
    "process": None,
    "start_time": None,
}

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRAPER_SCRIPT = PROJECT_ROOT / "glassdoor_scraper_unified.py"


def _find_chrome_path() -> Optional[str]:
    """Find Chrome executable."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def _is_port_open(port: int) -> bool:
    """Check if a port is open (Chrome debug port)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


@router.get("/scraper/status")
def scraper_status():
    """Get current scraper status and logs."""
    # Check if process is still alive
    proc = _scraper_state["process"]
    if proc and proc.poll() is not None:
        _scraper_state["running"] = False
        _scraper_state["process"] = None

    return {
        "running": _scraper_state["running"],
        "logs": _scraper_state["logs"][-200:],  # last 200 lines
        "start_time": _scraper_state["start_time"],
    }


@router.post("/scraper/start")
async def scraper_start(ports: str = "9222", mode: str = "matched", source_mode: str = "all", companies: Optional[str] = None):
    """Start the scraper process.

    Args:
        ports: Comma-separated Chrome debug ports
        mode: 'matched' or 'baseline'
        source_mode: 'all', 'office', 'country', or 'scan'
        companies: Comma-separated company names to filter (e.g., "ASUS,NVIDIA")
    """
    if _scraper_state["running"]:
        return {"error": "Scraper is already running"}

    port_list = [int(p.strip()) for p in ports.split(",")]

    # Verify Chrome debug ports are open
    closed_ports = [p for p in port_list if not _is_port_open(p)]
    if closed_ports:
        return {"error": f"Chrome debug ports not open: {closed_ports}. Please start Chrome with --remote-debugging-port first."}

    _scraper_state["logs"] = []
    _scraper_state["running"] = True
    _scraper_state["start_time"] = time.time()

    # Build command — always use manual mode (attach to existing Chrome)
    cmd = [
        sys.executable, str(SCRAPER_SCRIPT),
        "--mode", "manual",
        "--task", mode,  # mode from frontend is actually the task type (matched/baseline)
        "--ports", ",".join(str(p) for p in port_list),
        "--no-confirm",
    ]

    # Add source mode filter if specified (for matched mode only)
    if mode == "matched" and source_mode and source_mode != "all":
        cmd.extend(["--source-mode", source_mode])

    # Add company filter if specified
    if companies:
        cmd.extend(["--companies", companies])

    # Launch process with UTF-8 encoding
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(PROJECT_ROOT),
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    _scraper_state["process"] = proc

    # Read output in background
    asyncio.get_event_loop().run_in_executor(None, _read_output, proc)

    return {"status": "started", "ports": port_list, "mode": mode}


@router.post("/scraper/stop")
def scraper_stop():
    """Stop the running scraper and all child processes (ChromeDriver etc.)."""
    proc = _scraper_state["process"]
    if proc and proc.poll() is None:
        # Kill the entire process tree so ChromeDriver children are also terminated
        try:
            import psutil
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except Exception:
            # Fallback: just terminate the main process
            proc.kill()
        _scraper_state["logs"].append("[SYSTEM] Scraper terminated by user")
    _scraper_state["running"] = False
    _scraper_state["process"] = None
    return {"status": "stopped"}


@router.get("/scraper/check-login")
def check_login(port: int = 9222):
    """Check if Glassdoor login is active on given Chrome debug port."""
    if not _is_port_open(port):
        return {"logged_in": False, "error": f"Port {port} not open"}

    try:
        import urllib.request
        import json
        # Get list of tabs from Chrome DevTools
        url = f"http://127.0.0.1:{port}/json"
        with urllib.request.urlopen(url, timeout=3) as resp:
            tabs = json.loads(resp.read())

        glassdoor_tabs = [t for t in tabs if "glassdoor" in t.get("url", "").lower()]
        if not glassdoor_tabs:
            return {"logged_in": False, "message": "No Glassdoor tab found. Please navigate to glassdoor.com and log in."}

        # Check if any tab is on a login page
        login_indicators = ["login", "signin", "sign-in"]
        for tab in glassdoor_tabs:
            tab_url = tab.get("url", "").lower()
            if any(ind in tab_url for ind in login_indicators):
                return {"logged_in": False, "message": "Glassdoor login page detected. Please log in."}

        return {"logged_in": True, "message": f"Glassdoor session active on port {port}"}
    except Exception as e:
        return {"logged_in": False, "error": str(e)}


@router.get("/scraper/chrome-status")
def chrome_status():
    """Check Chrome debug instances."""
    ports = [9222, 9223, 9224]
    results = {}
    for port in ports:
        results[port] = _is_port_open(port)
    return results


@router.post("/scraper/close-chrome")
def close_chrome():
    """Close all Chrome debug instances launched by this dashboard."""
    import psutil
    closed = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline') or []
                cmdline_str = ' '.join(cmdline)
                if '--remote-debugging-port=' in cmdline_str:
                    proc.kill()
                    closed.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return {"status": "closed", "pids": closed}


@router.post("/scraper/launch-chrome")
def launch_chrome(port: int = 9222):
    """Launch Chrome with remote debugging on the given port, navigating to Glassdoor ASUS page."""
    if _is_port_open(port):
        return {"status": "already_running", "message": f"Chrome already running on port {port}"}

    chrome_path = _find_chrome_path()
    if not chrome_path:
        return {"status": "error", "message": "Chrome executable not found"}

    # Find the actual ASUS Glassdoor URL from matched data
    test_url = _get_asus_glassdoor_url()

    user_data_dir = os.path.expandvars(r"%USERPROFILE%\selenium\ChromeProfile" + (str(port) if port != 9222 else ""))
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        test_url,
    ]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "launched", "message": f"Chrome launched on port {port} → Glassdoor ASUS page"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _get_asus_glassdoor_url() -> str:
    """Get ASUS Glassdoor review URL from data files."""
    import json
    import glob
    # Check both office and other URL list files
    patterns = [
        str(PROJECT_ROOT / "data" / "asus_office.json"),
        str(PROJECT_ROOT / "data" / "*_office.json"),
        str(PROJECT_ROOT / "data" / "*_country.json"),
        str(PROJECT_ROOT / "data" / "*_scan.json"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    for item in data:
                        company = item.get('company', '') or ''
                        if 'ASUS' in company.upper() or 'asus' in f.lower():
                            url = item.get('url') or item.get('glassdoor_url', '')
                            if url and 'glassdoor.com' in url:
                                return url
        except Exception:
            continue
    return "https://www.glassdoor.com/Reviews/ASUS-Reviews-E40093.htm"


def _read_output(proc: subprocess.Popen):
    """Background reader for scraper stdout."""
    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            if line:
                _scraper_state["logs"].append(line)
    except Exception:
        pass
    finally:
        _scraper_state["running"] = False
        _scraper_state["process"] = None
