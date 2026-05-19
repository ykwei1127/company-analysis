"""
Settings & Company Management API endpoints.
Manages scraper config, company list, explore/match operations, and baseline locations.
"""
import json
import os
import subprocess
import sys
import threading
import glob
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Query

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
CONFIG_FILE = PROJECT_ROOT / "config.py"
COMPANY_FINDER_SCRIPT = PROJECT_ROOT / "company_finder.py"
BASELINE_FILE = DATA_DIR / "asus_locations.json"


# ─── Scraper Settings ───────────────────────────────────────────────

@router.get("/settings/config")
def get_config():
    """Read current config.py values."""
    config = _load_config()
    return {
        "include_baseline": config.get("INCLUDE_BASELINE", True),
        "parallel_ports": config.get("PARALLEL_PORTS", [9222, 9223, 9224]),
        "scraper_config": config.get("SCRAPER_CONFIG", {}),
        "output_config": config.get("OUTPUT_CONFIG", {}),
    }


@router.post("/settings/config")
def update_config(payload: dict):
    """Update config.py values."""
    config = _load_config()

    if "include_baseline" in payload:
        config["INCLUDE_BASELINE"] = payload["include_baseline"]
    if "parallel_ports" in payload:
        config["PARALLEL_PORTS"] = payload["parallel_ports"]
    if "scraper_config" in payload:
        config["SCRAPER_CONFIG"].update(payload["scraper_config"])

    _save_config(config)
    return {"status": "ok"}


# ─── Company List ───────────────────────────────────────────────────

@router.get("/settings/companies")
def list_companies():
    """List all matched companies (from data/*_matched*.json files)."""
    companies = []
    matched_files = sorted(glob.glob(str(DATA_DIR / "*_matched*.json")))
    for f in matched_files:
        basename = os.path.basename(f)
        # Derive display name: remove suffix like _matched.json or _matched_country.json
        name = basename.replace("_matched_country.json", "").replace("_matched.json", "").replace("_", " ").title()
        mode_label = "country" if "_country" in basename else "city"
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                entry_count = len(data) if isinstance(data, list) else 0
        except Exception:
            entry_count = 0
        companies.append({
            "name": name,
            "file": basename,
            "entries": entry_count,
            "mode": mode_label,
        })
    return {"companies": companies}


@router.delete("/settings/companies/{filename}")
def remove_company(filename: str):
    """Remove a company's matched JSON file."""
    filepath = DATA_DIR / filename
    if filepath.exists() and ("_matched" in filename and filename.endswith(".json")):
        filepath.unlink()
        return {"status": "deleted", "file": filename}
    return {"status": "error", "message": "File not found or invalid"}


# ─── Company Finder (Explore & Match) ──────────────────────────────

_finder_lock = threading.Lock()
_finder_state = {
    "process": None,
    "logs": [],
    "running": False,
    "mode": None,  # 'match', 'scan', 'explore'
}


@router.post("/settings/finder/match")
def run_match(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
    match_mode: Optional[str] = Query(None, description="Match mode: city or country")
):
    """Run company_finder.py match mode. match_mode: 'city' or 'country'."""
    # Parse comma-separated companies string to list
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    print(f"DEBUG: Received companies={companies_list}, match_mode={match_mode}")
    if _finder_state["running"]:
        return {"status": "already_running"}

    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "match"]
    if match_mode in ('city', 'country'):
        cmd += ['--mode', match_mode]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    # Pass selected companies via env var (comma-separated)
    if companies_list:
        env["FINDER_COMPANIES"] = ",".join(companies_list)

    _finder_state["logs"] = []
    _finder_state["running"] = True

    import threading

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT),
        env=env,
        encoding='utf-8',
        errors='replace',
    )
    _finder_state["process"] = proc

    def _reader():
        try:
            for line in proc.stdout:
                line = line.rstrip('\n')
                if line:
                    _finder_state["logs"].append(line)
        except Exception:
            pass
        finally:
            _finder_state["running"] = False

    threading.Thread(target=_reader, daemon=True).start()
    
    # Monitor thread to ensure running state is updated when process exits
    def _monitor():
        proc.wait()
        _finder_state["running"] = False
        print(f"Process exited with code {proc.returncode}")
    
    threading.Thread(target=_monitor, daemon=True).start()
    return {"status": "started"}


@router.post("/settings/finder/scan")
def run_scan(companies: Optional[List[str]] = None):
    """Run company_finder.py scan mode (scan all countries)."""
    if _finder_state["running"]:
        return {"status": "already_running"}

    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "scan"]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    # Pass selected companies via env var
    if companies:
        env["FINDER_COMPANIES"] = ",".join(companies)

    _finder_state["logs"] = []
    _finder_state["running"] = True

    import threading

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT),
        env=env,
        encoding='utf-8',
        errors='replace',
    )
    _finder_state["process"] = proc

    def _reader():
        try:
            for line in proc.stdout:
                line = line.rstrip('\n')
                if line:
                    with _finder_lock:
                        _finder_state["logs"].append(line)
        except Exception:
            pass
        finally:
            with _finder_lock:
                _finder_state["running"] = False

    threading.Thread(target=_reader, daemon=True).start()
    
    # Monitor thread to ensure running state is updated when process exits
    def _monitor():
        proc.wait()
        with _finder_lock:
            _finder_state["running"] = False
        print(f"Scan process exited with code {proc.returncode}")
    
    threading.Thread(target=_monitor, daemon=True).start()
    return {"status": "started"}


@router.post("/settings/finder/explore")
def run_explore(companies: Optional[List[str]] = None):
    """Run company_finder.py explore mode."""
    if _finder_state["running"]:
        return {"status": "already_running"}

    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "explore"]

    _run_finder_subprocess(cmd, "explore", companies=companies)
    return {"status": "started"}


@router.get("/settings/finder/status")
def get_finder_status():
    """Return current finder subprocess status and logs."""
    with _finder_lock:
        return {
            "running": _finder_state["running"],
            "mode": _finder_state["mode"],
            "logs": list(_finder_state["logs"]),  # Copy list to avoid race conditions
        }


@router.post("/settings/finder/stop")
def finder_stop():
    """Stop the running company_finder subprocess."""
    proc = _finder_state["process"]
    if proc and proc.poll() is None:
        try:
            import psutil
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except Exception:
            proc.kill()
    _finder_state["running"] = False
    _finder_state["process"] = None
    return {"status": "stopped"}


# ─── Baseline Locations ─────────────────────────────────────────────

@router.get("/settings/baseline")
def get_baseline():
    """Get ASUS baseline locations."""
    if not BASELINE_FILE.exists():
        return {"locations": []}
    with open(BASELINE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {"locations": data}


# ─── COMPANIES_TO_MATCH management ─────────────────────────────────

@router.get("/settings/companies-to-match")
def get_companies_to_match():
    """Read COMPANIES_TO_MATCH from company_finder.py."""
    try:
        # Use exec to extract the list
        ns = {}
        with open(COMPANY_FINDER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find COMPANIES_TO_MATCH block
        import re
        match = re.search(r'COMPANIES_TO_MATCH\s*=\s*\[', content)
        if not match:
            return {"companies": []}
        start = match.start()
        # Find matching bracket
        bracket_count = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == '[':
                bracket_count += 1
            elif content[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
        block = content[start:end]
        exec(block, ns)
        raw_list = ns.get('COMPANIES_TO_MATCH', [])

        # Normalize to list of dicts
        result = []
        for item in raw_list:
            if isinstance(item, str):
                result.append({"name": item})
            elif isinstance(item, dict):
                result.append(item)
        return {"companies": result}
    except Exception as e:
        return {"companies": [], "error": str(e)}


@router.post("/settings/companies-to-match/add")
def add_company_to_match(name: str):
    """Add a company name to COMPANIES_TO_MATCH in company_finder.py."""
    import re
    with open(COMPANY_FINDER_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the closing bracket of COMPANIES_TO_MATCH
    match = re.search(r'COMPANIES_TO_MATCH\s*=\s*\[', content)
    if not match:
        return {"status": "error", "message": "COMPANIES_TO_MATCH not found in company_finder.py"}

    # Find matching bracket
    bracket_count = 0
    end_idx = match.start()
    for i in range(match.start(), len(content)):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i
                break

    # Check if already exists
    block = content[match.start():end_idx + 1]
    if f"'{name}'" in block or f'"{name}"' in block:
        return {"status": "exists", "message": f"{name} already in list"}

    # Insert before the closing bracket
    new_entry = f"    '{name}',\n"
    new_content = content[:end_idx] + new_entry + content[end_idx:]

    with open(COMPANY_FINDER_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return {"status": "added", "name": name}


@router.post("/settings/companies-to-match/remove")
def remove_company_from_match(name: str):
    """Remove a company name from COMPANIES_TO_MATCH in company_finder.py and delete matched files."""
    import re
    with open(COMPANY_FINDER_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try to remove simple string entry: '    'Name',\n'
    patterns = [
        rf"    '{re.escape(name)}',\n",
        rf'    "{re.escape(name)}",\n',
        rf"    '{re.escape(name)}',\r\n",
        rf'    "{re.escape(name)}",\r\n',
    ]
    removed = False
    for pat in patterns:
        new_content = re.sub(pat, '', content)
        if new_content != content:
            content = new_content
            removed = True
            break

    if not removed:
        # Try removing a dict block with this name
        dict_pat = rf"\s*\{{[^}}]*'name':\s*'{re.escape(name)}'[^}}]*\}},?\n?"
        new_content = re.sub(dict_pat, '', content)
        if new_content != content:
            content = new_content
    
    # Write back the modified content
    with open(COMPANY_FINDER_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Also delete matched JSON files for this company
    files_removed = []
    safe_name = name.lower().replace(' ', '_')
    for suffix in ['_matched.json', '_matched_country.json', '_scan.json']:
        file_path = DATA_DIR / f"{safe_name}{suffix}"
        if file_path.exists():
            file_path.unlink()
            files_removed.append(file_path.name)
    
    return {"removed_from_list": removed, "files_removed": files_removed}


# ─── Helpers ────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load config.py as a dict."""
    ns = {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            exec(f.read(), ns)
    except Exception:
        pass
    return {
        "INCLUDE_BASELINE": ns.get("INCLUDE_BASELINE", True),
        "PARALLEL_PORTS": ns.get("PARALLEL_PORTS", [9222, 9223, 9224]),
        "SCRAPER_CONFIG": ns.get("SCRAPER_CONFIG", {}),
        "OUTPUT_CONFIG": ns.get("OUTPUT_CONFIG", {}),
    }


def _save_config(config: dict):
    """Write config back to config.py."""
    lines = [
        "# Glassdoor 爬蟲配置文件\n",
        "\n",
        "INCLUDE_BASELINE = {}\n".format(repr(config["INCLUDE_BASELINE"])),
        "\n",
        "PARALLEL_PORTS = {}\n".format(repr(config["PARALLEL_PORTS"])),
        "\n",
        "SCRAPER_CONFIG = {}\n".format(_format_dict(config["SCRAPER_CONFIG"])),
        "\n",
        "OUTPUT_CONFIG = {}\n".format(_format_dict(config["OUTPUT_CONFIG"])),
    ]
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def _format_dict(d: dict) -> str:
    """Format a dict for writing to config.py."""
    if not d:
        return "{}"
    items = []
    for k, v in d.items():
        items.append(f"    {repr(k)}: {repr(v)},")
    return "{\n" + "\n".join(items) + "\n}"
