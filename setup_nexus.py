"""
setup_nexus.py — Core Nexus Automatic Setup
Run this once after cloning the repo. It does everything for you:
  1. Checks Python version
  2. Installs all dependencies
  3. Checks for / starts Ollama
  4. Pulls the AI model
  5. Builds a config.json personalised to YOUR system
  6. Creates a desktop shortcut
  7. Runs a quick test

Usage:
  python setup_nexus.py
"""

import os
import sys
import json
import time
import string
import shutil
import platform
import subprocess
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Colours for terminal output ───────────────────────────────────────────────
def green(s):  return f"\033[92m{s}\033[0m"
def cyan(s):   return f"\033[96m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def red(s):    return f"\033[91m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"

def ok(msg):   print(f"  {green('[OK]')} {msg}")
def warn(msg): print(f"  {yellow('[WARN]')} {msg}")
def err(msg):  print(f"  {red('[ERROR]')} {msg}")
def info(msg): print(f"  {cyan('[INFO]')} {msg}")
def step(n, msg): print(f"\n{bold(cyan(f'── STEP {n}'))} {bold(msg)}")


def banner():
    print(cyan("""
  ╔══════════════════════════════════════════════╗
  ║       CORE NEXUS — Automatic Setup           ║
  ║   This will set everything up for you.       ║
  ╚══════════════════════════════════════════════╝
"""))


# ── Step 1: Python version check ─────────────────────────────────────────────
def check_python():
    step(1, "Checking Python version")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        err(f"Python 3.10+ required. You have {v.major}.{v.minor}.")
        err("Download Python 3.12 from https://python.org/downloads/")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


# ── Step 2: Install dependencies ─────────────────────────────────────────────
def install_deps():
    step(2, "Installing Python dependencies")

    packages = [
        "SpeechRecognition",
        "pyttsx3",
        "pyaudio",
        "psutil",
        "pycaw",
        "comtypes",
        "flask",
        "flask-socketio",
        "mss",
        "pillow",
        "selenium",
        "webdriver-manager",
        "piper-tts",
        "sounddevice",
        "soundfile",
        "numpy",
        "openwakeword",
        "pygetwindow",
        "pywin32",
        "requests",
    ]

    failed = []
    for pkg in packages:
        print(f"  Installing {pkg}...", end="\r")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            capture_output=True
        )
        if result.returncode == 0:
            ok(f"Installed {pkg}                    ")
        else:
            # Try pipwin for pyaudio
            if pkg == "pyaudio":
                warn("pyaudio failed — trying pipwin...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pipwin", "--quiet"])
                result2 = subprocess.run(
                    [sys.executable, "-m", "pipwin", "install", "pyaudio"],
                    capture_output=True
                )
                if result2.returncode == 0:
                    ok("Installed pyaudio via pipwin")
                    continue
            warn(f"Could not install {pkg} — continuing")
            failed.append(pkg)

    if failed:
        warn(f"Some packages failed: {', '.join(failed)}")
        warn("You can install them manually later with: pip install <package>")
    else:
        ok("All dependencies installed")


# ── Step 3: Check Ollama ──────────────────────────────────────────────────────
def check_ollama():
    step(3, "Checking Ollama")

    # Check if ollama executable exists
    ollama_exe = shutil.which("ollama")
    if not ollama_exe:
        warn("Ollama not found in PATH.")
        print(f"\n  {yellow('Please install Ollama manually:')}")
        print(f"  1. Go to {cyan('https://ollama.com')} and download the installer")
        print(f"  2. Run the installer")
        print(f"  3. Run this setup script again")
        print()
        ans = input("  Have you installed Ollama already? (y/n): ").strip().lower()
        if ans != "y":
            warn("Skipping Ollama setup. Install it and re-run this script.")
            return False

    # Check if Ollama is running
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=3)
        ok("Ollama is running")
        return True
    except Exception:
        info("Ollama not running — starting it...")
        try:
            subprocess.Popen(["ollama", "serve"],
                             creationflags=subprocess.CREATE_NEW_CONSOLE
                             if sys.platform == "win32" else 0)
            time.sleep(3)
            urllib.request.urlopen("http://localhost:11434", timeout=5)
            ok("Ollama started")
            return True
        except Exception as e:
            warn(f"Could not start Ollama: {e}")
            warn("Start Ollama manually and re-run this script.")
            return False


# ── Step 4: Pull AI model ─────────────────────────────────────────────────────
def pull_model():
    step(4, "Pulling AI model (gemma3:4b)")

    # Check if already pulled
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "gemma3:4b" in result.stdout:
        ok("gemma3:4b already downloaded")
        return

    info("Downloading gemma3:4b (~3GB) — this may take a few minutes...")
    result = subprocess.run(["ollama", "pull", "gemma3:4b"])
    if result.returncode == 0:
        ok("gemma3:4b downloaded successfully")
    else:
        warn("Model download failed. Run manually: ollama pull gemma3:4b")


# ── Step 5: Build personalised config.json ────────────────────────────────────
def build_config():
    step(5, "Building personalised config.json for your system")

    username = os.environ.get("USERNAME") or os.environ.get("USER") or "user"
    ok(f"Detected username: {username}")

    # Find available drives
    drives = []
    if sys.platform == "win32":
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        ok(f"Found drives: {', '.join(drives)}")

    # Detect common app paths
    def find_path(*candidates):
        for c in candidates:
            expanded = c.replace("%USERNAME%", username).replace("%USERPROFILE%", os.path.expanduser("~"))
            if os.path.exists(expanded):
                return expanded
        return ""

    # Build apps dict with detected paths
    apps = {}

    # Discord
    discord_path = find_path(
        f"C:\\Users\\{username}\\AppData\\Local\\Discord\\Update.exe",
        f"D:\\Users\\{username}\\AppData\\Local\\Discord\\Update.exe",
    )
    if discord_path:
        apps["discord"] = {"path": discord_path, "description": "Discord",
                           "flags": ["--processStart", "Discord.exe"]}
        ok(f"Found Discord: {discord_path}")

    # Chrome
    chrome_path = find_path(
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    )
    if chrome_path:
        apps["chrome"] = {"path": chrome_path, "description": "Google Chrome", "flags": []}
        apps["google chrome"] = apps["chrome"].copy()
        ok(f"Found Chrome: {chrome_path}")

    # Spotify
    spotify_path = find_path(
        f"C:\\Users\\{username}\\AppData\\Roaming\\Spotify\\Spotify.exe",
    )
    if spotify_path:
        apps["spotify"] = {"path": spotify_path, "description": "Spotify", "flags": []}
        ok(f"Found Spotify: {spotify_path}")

    # VS Code
    vscode_path = find_path(
        f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
        "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    )
    if vscode_path:
        apps["vscode"] = {"path": vscode_path, "description": "Visual Studio Code", "flags": []}
        apps["visual studio code"] = apps["vscode"].copy()
        ok(f"Found VS Code: {vscode_path}")

    # Edge
    edge_path = find_path(
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    )
    if edge_path:
        apps["edge"] = {"path": edge_path, "description": "Microsoft Edge", "flags": []}
        ok(f"Found Edge: {edge_path}")

    # Steam
    steam_path = find_path(
        "C:\\Program Files (x86)\\Steam\\steam.exe",
        "C:\\Program Files\\Steam\\steam.exe",
    )
    for d in drives:
        if not steam_path:
            steam_path = find_path(f"{d}Steam\\steam.exe", f"{d}Program Files\\Steam\\steam.exe")
    if steam_path:
        apps["steam"] = {"path": steam_path, "description": "Steam", "flags": []}
        ok(f"Found Steam: {steam_path}")

    # Epic Games
    epic_path = find_path(
        "C:\\Program Files (x86)\\Epic Games\\Launcher\\Portal\\Binaries\\Win32\\EpicGamesLauncher.exe",
        "C:\\Program Files\\Epic Games\\Launcher\\Portal\\Binaries\\Win64\\EpicGamesLauncher.exe",
    )
    if epic_path:
        apps["epic games"] = {"path": epic_path, "description": "Epic Games Launcher", "flags": []}
        ok(f"Found Epic Games: {epic_path}")

    # Common Steam games (protocol-based — always work if Steam is installed)
    steam_games = {
        "war thunder":           ("steam://rungameid/236390",  "War Thunder",           "high"),
        "geometry dash":         ("steam://rungameid/322170",  "Geometry Dash",         None),
        "rainbow six siege":     ("steam://rungameid/359550",  "Rainbow Six Siege",     "high"),
        "siege":                 ("steam://rungameid/359550",  "Rainbow Six Siege",     "high"),
        "the stanley parable":   ("steam://rungameid/1569580", "The Stanley Parable",   None),
        "stanley parable":       ("steam://rungameid/1569580", "The Stanley Parable",   None),
        "roblox":                ("steam://rungameid/1778820", "Roblox",                None),
        "peggle deluxe":         ("steam://rungameid/3560",    "Peggle Deluxe",         None),
        "pc building simulator": ("steam://rungameid/621060",  "PC Building Simulator", None),
        "source filmmaker":      ("steam://rungameid/1840",    "Source Filmmaker",      None),
        "sfm":                   ("steam://rungameid/1840",    "Source Filmmaker",      None),
        "liar's bar":            ("steam://rungameid/3097560", "Liar's Bar",            "high"),
        "poppy playtime":        ("steam://rungameid/1721470", "Poppy Playtime",        None),
        "r.e.p.o":               ("steam://rungameid/3241660", "R.E.P.O.",              None),
        "repo":                  ("steam://rungameid/3241660", "R.E.P.O.",              None),
    }
    for key, (path, desc, priority) in steam_games.items():
        entry = {"path": path, "description": desc, "flags": []}
        if priority:
            entry["priority"] = priority
        apps[key] = entry

    # Fortnite (Epic)
    apps["fortnite"] = {
        "path": "com.epicgames.launcher://apps/fn?action=launch&silent=true",
        "description": "Fortnite (Epic Games)",
        "priority": "high",
        "flags": []
    }

    # GitHub Desktop
    github_path = find_path(
        f"C:\\Users\\{username}\\AppData\\Local\\GitHubDesktop\\GitHubDesktop.exe",
    )
    if github_path:
        apps["github desktop"] = {"path": github_path, "description": "GitHub Desktop", "flags": []}
        apps["github"] = apps["github desktop"].copy()
        ok(f"Found GitHub Desktop: {github_path}")

    # MSI Afterburner
    msi_path = find_path("C:\\Program Files (x86)\\MSI Afterburner\\MSIAfterburner.exe")
    if msi_path:
        apps["msi afterburner"] = {"path": msi_path, "description": "MSI Afterburner", "flags": []}
        apps["afterburner"] = apps["msi afterburner"].copy()
        ok(f"Found MSI Afterburner: {msi_path}")

    # Detect nircmd
    nircmd_path = ""
    for d in drives:
        candidate = os.path.join(d, "Tools", "nircmd", "nircmd.exe")
        if os.path.exists(candidate):
            nircmd_path = candidate
            break

    # Browser path for tools
    browser_path = chrome_path or edge_path or ""

    # Build final config
    config = {
        "_comment": "Auto-generated by setup_nexus.py. Edit paths as needed.",
        "_username": username,
        "wake_keyword": "hey_jarvis",
        "_wake_note": "Options: hey_jarvis, alexa, hey_mycroft — or train a custom model",
        "apps": apps,
        "macros": {
            "game mode": {
                "description": "Launch Discord, set volume to 60",
                "actions": [
                    {"type": "volume", "level": 60},
                    {"type": "launch", "key": "discord"},
                    {"type": "speak",  "text": "Game mode activated. Discord launched."}
                ]
            },
            "study mode": {
                "description": "Close games and Discord, reduce volume",
                "actions": [
                    {"type": "kill",   "process": "Discord.exe", "name": "Discord"},
                    {"type": "volume", "level": 30},
                    {"type": "speak",  "text": "Study mode active. Distractions eliminated."}
                ]
            },
            "night mode": {
                "description": "Low volume, wind down",
                "actions": [
                    {"type": "volume", "level": 15},
                    {"type": "speak",  "text": "Night mode engaged. Volume reduced."}
                ]
            }
        },
        "notifications": {
            "cpu_threshold": 90,
            "gpu_temp_threshold": 85,
            "break_interval_min": 120
        },
        "tools": {
            "browser": browser_path,
            "nircmd":  nircmd_path,
            "_note":   "nircmd optional — volume fallback. Download from nirsoft.net"
        }
    }

    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    ok(f"config.json written with {len(apps)} apps detected")
    info("You can add more apps manually in config.json at any time")


# ── Step 6: PowerShell execution policy ──────────────────────────────────────
def set_execution_policy():
    step(6, "Setting PowerShell execution policy")
    if sys.platform != "win32":
        info("Not Windows — skipping")
        return
    result = subprocess.run(
        ["powershell", "-Command",
         "Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force"],
        capture_output=True
    )
    if result.returncode == 0:
        ok("PowerShell execution policy set")
    else:
        warn("Could not set execution policy — you may need to run this manually:")
        warn("Set-ExecutionPolicy -Scope CurrentUser RemoteSigned")


# ── Step 7: Create desktop shortcut ──────────────────────────────────────────
def create_shortcut():
    step(7, "Creating desktop shortcut")
    if sys.platform != "win32":
        info("Not Windows — skipping shortcut creation")
        return

    launcher   = os.path.join(BASE_DIR, "launcher.pyw")
    pythonw    = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    desktop    = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut   = os.path.join(desktop, "Core Nexus.lnk")

    if not os.path.exists(pythonw):
        pythonw = sys.executable  # fallback

    ps_cmd = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut}"); '
        f'$s.TargetPath = "{pythonw}"; '
        f'$s.Arguments = \'"{launcher}"\'; '
        f'$s.WorkingDirectory = "{BASE_DIR}"; '
        f'$s.Description = "Launch Core Nexus AI"; '
        f'$s.Save()'
    )
    result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
    if os.path.exists(shortcut):
        ok(f"Shortcut created on Desktop")
    else:
        warn("Shortcut creation failed — double-click launcher.pyw directly")


# ── Step 8: Quick test ────────────────────────────────────────────────────────
def quick_test():
    step(8, "Running quick system test")

    tests = [
        ("flask",             "Web server"),
        ("speech_recognition","Voice recognition"),
        ("psutil",            "Process management"),
        ("mss",               "Screen capture"),
    ]

    all_ok = True
    for module, name in tests:
        try:
            __import__(module)
            ok(name)
        except ImportError:
            warn(f"{name} — import failed (pip install {module})")
            all_ok = False

    # Ollama
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        ok("Ollama connection")
    except Exception:
        warn("Ollama not reachable — start it with: ollama serve")
        all_ok = False

    return all_ok


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    banner()
    print(f"  Setting up Core Nexus in: {cyan(BASE_DIR)}\n")

    check_python()
    install_deps()
    ollama_ok = check_ollama()
    if ollama_ok:
        pull_model()
    build_config()
    set_execution_policy()
    create_shortcut()
    all_ok = quick_test()

    print(f"\n{bold(cyan('── Setup Complete ─────────────────────────────────────'))}")
    if all_ok:
        print(f"\n  {green('Everything is ready!')} Double-click {cyan('Core Nexus')} on your Desktop to start.")
    else:
        print(f"\n  {yellow('Setup finished with some warnings.')} Check the output above.")
    print(f"\n  Or launch manually:")
    print(f"  {cyan('python core_nexus.py')}       — voice mode")
    print(f"  {cyan('python core_nexus.py --text')} — text mode (no mic needed)")
    print(f"  {cyan('python nexus_server.py')}      — web dashboard at localhost:8080")
    print()


if __name__ == "__main__":
    main()
