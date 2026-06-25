"""
Settings & Company Management API endpoints.
Manages scraper config, company list, URL list building (office/country/city/scan/mix), and baseline locations.
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
BASELINE_FILE = DATA_DIR / "asus_office.json"


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
    """List all company URL list files (office/country/city/scan/mix)."""
    companies = []
    # Match all five types of URL list files
    for pattern in ["*_office.json", "*_country.json", "*_city.json", "*_scan.json", "*_mix.json"]:
        for f in sorted(glob.glob(str(DATA_DIR / pattern))):
            basename = os.path.basename(f)
            # Derive display name from filename
            name = basename.replace("_office.json", "").replace("_country.json", "").replace("_city.json", "").replace("_scan.json", "").replace("_mix.json", "").replace("_", " ").title()
            # Determine list type from suffix
            if basename.endswith("_office.json"):
                list_type = "office"
            elif basename.endswith("_country.json"):
                list_type = "country"
            elif basename.endswith("_city.json"):
                list_type = "city"
            elif basename.endswith("_scan.json"):
                list_type = "scan"
            elif basename.endswith("_mix.json"):
                list_type = "mix"
            else:
                list_type = "unknown"
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
                "mode": list_type,  # Keep 'mode' key for backward compat with scraper page
            })
    return {"companies": companies}


@router.delete("/settings/companies/{filename}")
def remove_company(filename: str):
    """Remove a company's URL list JSON file."""
    filepath = DATA_DIR / filename
    valid_suffixes = ("_office.json", "_country.json", "_city.json", "_scan.json", "_mix.json")
    if filepath.exists() and any(filename.endswith(s) for s in valid_suffixes):
        filepath.unlink()
        return {"status": "deleted", "file": filename}
    return {"status": "error", "message": "File not found or invalid"}


# ─── Company Finder (Office / Country / Scan) ──────────────────────

_finder_lock = threading.Lock()
_finder_state = {
    "process": None,
    "logs": [],
    "running": False,
    "mode": None,  # 'office', 'country', 'scan'
}


def _run_finder_subprocess(cmd, mode, companies=None):
    """Shared helper to launch company_finder.py subprocess."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    if companies:
        env["FINDER_COMPANIES"] = ",".join(companies)

    # Pass parallel ports from config.py so company_finder can use multiple Chrome instances
    config = _load_config()
    parallel_ports = config.get("PARALLEL_PORTS", [9222, 9223, 9224])
    if parallel_ports:
        env["FINDER_PORTS"] = ",".join(str(p) for p in parallel_ports)

    _finder_state["logs"] = []
    _finder_state["running"] = True
    _finder_state["mode"] = mode

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

    def _monitor():
        proc.wait()
        with _finder_lock:
            _finder_state["running"] = False
        print(f"Finder ({mode}) process exited with code {proc.returncode}")

    threading.Thread(target=_monitor, daemon=True).start()


@router.post("/settings/finder/office")
def run_finder_office(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
):
    """Run company_finder.py office mode (build office location URL lists)."""
    if _finder_state["running"]:
        return {"status": "already_running"}
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "office"]
    _run_finder_subprocess(cmd, "office", companies=companies_list)
    return {"status": "started"}


@router.post("/settings/finder/country")
def run_finder_country(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
):
    """Run company_finder.py country mode (build country-level URL lists)."""
    if _finder_state["running"]:
        return {"status": "already_running"}
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "country"]
    _run_finder_subprocess(cmd, "country", companies=companies_list)
    return {"status": "started"}


@router.post("/settings/finder/scan")
def run_finder_scan(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
):
    """Run company_finder.py scan mode (scan all countries)."""
    if _finder_state["running"]:
        return {"status": "already_running"}
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "scan"]
    _run_finder_subprocess(cmd, "scan", companies=companies_list)
    return {"status": "started"}


@router.post("/settings/finder/city")
def run_finder_city(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
):
    """Run company_finder.py city mode (ASUS-baseline city-level match)."""
    if _finder_state["running"]:
        return {"status": "already_running"}
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "city"]
    _run_finder_subprocess(cmd, "city", companies=companies_list)
    return {"status": "started"}


@router.post("/settings/finder/mix")
def run_finder_mix(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
):
    """Run company_finder.py mix mode (merge office/country/city lists)."""
    if _finder_state["running"]:
        return {"status": "already_running"}
    companies_list = [c.strip() for c in companies.split(',') if c.strip()] if companies else None
    cmd = [str(VENV_PYTHON), str(COMPANY_FINDER_SCRIPT), "mix"]
    _run_finder_subprocess(cmd, "mix", companies=companies_list)
    return {"status": "started"}


# Legacy endpoint aliases for backward compatibility
@router.post("/settings/finder/match")
def run_match_legacy(
    companies: Optional[str] = Query(None, description="Comma-separated company names"),
    match_mode: Optional[str] = Query(None, description="Match mode: city or country")
):
    """Legacy match endpoint — routes to office or country."""
    if match_mode == 'city':
        return run_finder_office(companies=companies)
    return run_finder_country(companies=companies)


@router.post("/settings/finder/explore")
def run_explore_legacy(companies: Optional[List[str]] = None):
    """Legacy explore endpoint — routes to office."""
    companies_str = ",".join(companies) if companies else None
    return run_finder_office(companies=companies_str)


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
def get_baseline(file: Optional[str] = Query(None, description="URL list filename to view")):
    """Get URL list entries from a specific file, or ASUS office locations by default."""
    if file:
        # Validate filename to prevent path traversal
        valid_suffixes = ("_office.json", "_country.json", "_city.json", "_scan.json", "_mix.json")
        if not any(file.endswith(s) for s in valid_suffixes):
            return {"locations": []}
        filepath = DATA_DIR / file
    else:
        filepath = BASELINE_FILE
    if not filepath.exists():
        return {"locations": []}
    with open(filepath, 'r', encoding='utf-8') as f:
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
    for suffix in ['_office.json', '_country.json', '_city.json', '_scan.json', '_mix.json']:
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
