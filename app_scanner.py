"""
app_scanner.py — Core Nexus Startup App Scanner
Scans all drives on startup and builds/updates app_cache.json.
Fast: skips system dirs, limits depth, caches results.
"""

import os
import json
import time
import string
import subprocess
from pathlib import Path

CACHE_PATH   = os.path.join(os.path.dirname(__file__), "app_cache.json")
MAX_DEPTH    = 6

# Directories to skip entirely (system, temp, junk)
SKIP_DIRS = {
    "windows", "system32", "syswow64", "winsxs", "windowsapps",
    "$recycle.bin", "system volume information", "recovery",
    "perflogs", "msocache", "$windows.~bt", "$windows.~ws",
    "intel", "amd", "nvidia", "config.msi", "boot",
    "node_modules", "__pycache__", ".git", ".vs",
    "temp", "tmp", "cache", "log", "logs",
}

# EXE names to ignore (installers, updaters, helpers — not launchable apps)
IGNORE_EXE_FRAGMENTS = {
    "unins", "uninst", "setup", "install", "update", "updater",
    "crashreport", "crash_report", "helper", "redist", "vcredist",
    "directx", "dotnet", "dxsetup", "vc_red", "windowsapp",
    "svchost", "taskhost", "conhost", "dllhost", "werfault",
}


def get_all_drives() -> list[str]:
    """Return all available drive letters."""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def exe_is_launchable(fname: str) -> bool:
    """Filter out obvious non-app executables."""
    fl = fname.lower()
    return not any(frag in fl for frag in IGNORE_EXE_FRAGMENTS)


def name_to_key(fname: str) -> str:
    """Convert filename to a lookup key: strip .exe, lowercase, clean."""
    key = fname.lower()
    key = key.replace(".exe", "").replace(".url", "").replace(".lnk", "")
    key = key.replace("-", " ").replace("_", " ").replace(".", " ")
    # Strip common suffixes
    for suffix in [" x64", " x86", " win64", " win32", " 64bit", " 32bit",
                   " launcher", " desktop", " app"]:
        if key.endswith(suffix):
            key = key[:-len(suffix)].strip()
    return key.strip()


def scan_drive(drive: str, existing_cache: dict) -> dict:
    """
    Walk a single drive and collect launchable .exe, .url, .lnk files.
    Returns {key: path} dict of found apps.
    """
    found = {}
    print(f"  [SCAN] Drive {drive} ...", end=" ", flush=True)
    count = 0

    # Also check Desktop for .url and .lnk shortcuts
    username = os.environ.get("USERNAME", "")
    desktops = []
    if username:
        desktops = [
            f"C:\\Users\\{username}\\Desktop",
            "C:\\Users\\Public\\Desktop",
        ]

    # Scan desktop shortcuts first
    for desktop in desktops:
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                fl = fname.lower()
                if fl.endswith(".url") or fl.endswith(".lnk"):
                    key = name_to_key(fname)
                    path = os.path.join(desktop, fname)
                    found[key] = path
                    count += 1
        except PermissionError:
            pass

    try:
        for dirpath, dirnames, filenames in os.walk(drive):
            # Depth guard
            depth = dirpath.replace(drive, "").count(os.sep)
            if depth >= MAX_DEPTH:
                dirnames.clear()
                continue

            # Skip junk directories
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in SKIP_DIRS and not d.startswith(".")
            ]

            for fname in filenames:
                fl = fname.lower()
                if fl.endswith(".exe") and exe_is_launchable(fname):
                    key  = name_to_key(fname)
                    path = os.path.join(dirpath, fname)
                    # Prefer shorter paths (usually the main exe, not a subfolder helper)
                    if key not in found or len(path) < len(found[key]):
                        found[key] = path
                        count += 1

    except (PermissionError, OSError):
        pass

    print(f"{count} apps found")
    return found


def build_cache(force: bool = False) -> dict:
    """
    Load existing cache, scan all drives, merge results.
    Skips scan if cache is less than 24h old and force=False.
    """
    existing = {}
    cache_age = float("inf")

    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                data = json.load(f)
            existing  = data.get("apps", {})
            scanned   = data.get("scanned_at", 0)
            cache_age = time.time() - scanned
        except Exception:
            pass

    if not force and cache_age < 86400 and existing:
        print(f"  [SCAN] App cache valid ({len(existing)} entries). Skipping re-scan.")
        return existing

    print(f"  [SCAN] Building app cache across all drives...")
    t0 = time.time()

    merged = dict(existing)  # start from existing, overwrite with fresh finds
    for drive in get_all_drives():
        try:
            found = scan_drive(drive, existing)
            merged.update(found)
        except Exception as e:
            print(f"  [SCAN] Drive {drive} error: {e}")

    # Save cache
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump({"scanned_at": time.time(), "apps": merged}, f, indent=2)
        print(f"  [SCAN] Cache saved: {len(merged)} apps in {time.time()-t0:.1f}s → {CACHE_PATH}")
    except Exception as e:
        print(f"  [SCAN] Could not save cache: {e}")

    return merged


def find_in_cache(name: str, cache: dict) -> str | None:
    """
    Look up a name in the cache using exact then fuzzy matching.
    Returns path if found, None otherwise.
    """
    import difflib

    name_key = name_to_key(name + ".exe")  # normalise query same way as keys

    # 1. Exact match
    if name_key in cache:
        return cache[name_key]

    # 2. Substring match
    for key, path in cache.items():
        if name_key in key or key in name_key:
            return path

    # 3. Fuzzy match (handles typos / speech errors)
    keys = list(cache.keys())
    matches = difflib.get_close_matches(name_key, keys, n=1, cutoff=0.6)
    if matches:
        print(f"  [FUZZY] '{name_key}' matched to '{matches[0]}' in cache")
        return cache[matches[0]]

    return None


if __name__ == "__main__":
    # Run standalone to pre-build cache
    cache = build_cache(force=True)
    print(f"\nTotal apps indexed: {len(cache)}")
    # Print a sample
    sample = list(cache.items())[:20]
    for k, v in sample:
        print(f"  {k:40s} → {v}")
