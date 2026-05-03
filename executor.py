"""
executor.py — Core Nexus Action Executor
Handles all OS-level dispatch: launch, volume, URL, kill, power, thermal, macro.
"""

import os
import sys
import subprocess
import webbrowser
import time
import glob

from fuzzy_match import correct_speech, FailureTracker
from app_scanner import find_in_cache, build_cache
from usage_tracker import UsageTracker


try:
    from window_manager import dispatch_window_action
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False

# Global usage tracker
_USAGE_TRACKER = UsageTracker()

try:
    from screen_vision import describe_screen, analyse_screen, list_monitors
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    from food_ordering import order_food, find_reservation, match_restaurant
    FOOD_AVAILABLE = True
except ImportError:
    FOOD_AVAILABLE = False

# Global app cache (populated on first use / startup)
_APP_CACHE: dict = {}
_FAILURE_TRACKER = FailureTracker()

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False


# Common search roots across all drives
SEARCH_ROOTS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\XboxGames",
    "C:\\Program Files (x86)\\Steam\\steamapps\\common",
    "D:\\Program Files",
    "D:\\Program Files (x86)",
    "D:\\Games",
    "D:\\SteamLibrary\\steamapps\\common",
    "E:\\Program Files",
    "E:\\Games",
    "E:\\SteamLibrary\\steamapps\\common",
    "F:\\Games",
    "F:\\Program Files",
    "F:\\SteamLibrary\\steamapps\\common",
    "F:\\Steam\\steamapps\\common",
    "G:\\SteamLibrary\\steamapps\\common",
]

# Add per-user paths dynamically
_username = os.environ.get("USERNAME", "")
if _username:
    SEARCH_ROOTS += [
        f"C:\\Users\\{_username}\\Desktop",
        f"C:\\Users\\{_username}\\AppData\\Local",
        f"C:\\Users\\{_username}\\AppData\\Roaming",
        f"C:\\Users\\{_username}\\AppData\\Local\\Programs",
    ]


def find_shortcut(name: str) -> str | None:
    """
    Search Desktop (user + public) for a .url or .lnk shortcut matching name.
    Checked before filesystem exe search — handles Steam/Epic shortcuts.
    """
    username = os.environ.get("USERNAME", "")
    desktops = [
        f"C:\\Users\\{username}\\Desktop",
        "C:\\Users\\Public\\Desktop",
    ]
    name_lower = name.lower()
    for desktop in desktops:
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                fl = fname.lower()
                if fl.endswith(".url") or fl.endswith(".lnk"):
                    stem = fl.replace(".url", "").replace(".lnk", "").strip()
                    if name_lower in stem or stem in name_lower:
                        full = os.path.join(desktop, fname)
                        print(f"  [FIND] Desktop shortcut: {full}")
                        return full
        except PermissionError:
            continue
    return None


def find_exe(name: str) -> str | None:
    """
    Search common install locations for an executable by name.
    Returns full path if found, None otherwise.
    name can be partial e.g. 'minecraft', 'trackmania'
    """
    name_lower = name.lower().replace(".exe", "")

    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                for fname in filenames:
                    if fname.lower().endswith(".exe") and name_lower in fname.lower():
                        full = os.path.join(dirpath, fname)
                        print(f"  [FIND] Found: {full}")
                        return full
                # Don't recurse too deep — keeps it fast
                depth = dirpath.replace(root, "").count(os.sep)
                if depth >= 4:
                    dirnames.clear()
        except PermissionError:
            continue

    # Also try Windows registry via where.exe
    try:
        result = subprocess.run(
            ["where", name_lower + ".exe"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            path = result.stdout.strip().splitlines()[0]
            print(f"  [FIND] Found via where: {path}")
            return path
    except Exception:
        pass

    return None


class ActionExecutor:
    def __init__(self, config: dict, speaker):
        self.config    = config
        self.speaker   = speaker
        self.failures  = _FAILURE_TRACKER
        self.app_cache = _APP_CACHE
        self.usage     = _USAGE_TRACKER


    def execute(self, action: dict):
        t = action.get("type", "")
        dispatch = {
            "launch":   self._launch,
            "volume":   self._volume,
            "url":      self._url,
            "search":   self._search,
            "kill":     self._kill,
            "power":    self._power,
            "thermal":  self._thermal,
            "macro":    self._macro,
            "speak":    self._speak,
            "vision":   self._vision,
            "food":     self._food,
            "window":   self._window,
            "reminder": self._reminder,
        }
        handler = dispatch.get(t)
        if handler:
            try:
                handler(action)
            except Exception as e:
                msg = f"Execution failed. Reason: {e}"
                print(f"  [ERROR] {msg}")
                self.speaker.say(msg)
        else:
            print(f"  [WARN] Unknown action type: {t}")

    def _launch(self, action: dict):
        raw_key  = action.get("key", "").lower()
        apps     = self.config.get("apps", {})

        # ── Step 1: Correct speech recognition errors ─────────────────────────
        known_keys = list(apps.keys()) + list(self.app_cache.keys())
        key = correct_speech(raw_key, known_keys)

        # ── Step 2: Check if we have a previously-resolved working path ────────
        resolved = self.failures.get_resolved_path(key)
        if resolved and os.path.exists(resolved):
            print(f"  [ADAPT] Using previously resolved path for '{key}': {resolved}")
            path = resolved
            flags = []
            priority = None
        else:
            # ── Step 3: Fuzzy match against config keys ─────────────────────────
            if key not in apps:
                matches = [k for k in apps if key in k or k in key]
                if matches:
                    key = matches[0]

            path     = None
            flags    = []
            priority = None

            if key in apps:
                app      = apps[key]
                path     = app.get("path", "")
                flags    = app.get("flags", [])
                priority = app.get("priority", None)

        # steam:// protocol — skip filesystem check entirely
        if path and path.lower().startswith("steam://"):
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
            print(f"  [LAUNCH] {key} via Steam protocol: {path}")
            return

        # If path from config doesn't exist, search for shortcuts then exe
        if not path or (not path.lower().startswith("steam://") and
                        not path.lower().startswith("com.epicgames") and
                        not os.path.exists(path)):
            if path:
                print(f"  [WARN] Config path not found: {path}. Searching...")
            else:
                print(f"  [INFO] No config entry for '{key}'. Searching...")

            search_term = key if key else action.get("key", "")

            # Skip previously failed paths
            failed_paths = self.failures.get_failed_paths(key)

            # 1. Check app cache (pre-built on startup)
            found = find_in_cache(search_term, self.app_cache)
            if found and found in failed_paths:
                found = None  # skip known-bad path

            # 2. Check Desktop shortcuts
            if not found:
                found = find_shortcut(search_term)

            # 3. Fall back to live filesystem scan
            if not found:
                found = find_exe(search_term)
                if found and found in failed_paths:
                    found = None

            if found:
                path = found
                if key not in apps:
                    apps[key] = {"path": found, "description": key, "flags": [], "priority": None}
                else:
                    apps[key]["path"] = found
                self.config["apps"] = apps
                print(f"  [AUTO] Path resolved to: {found}")
            else:
                self.failures.record_failure(key, path or "")
                self.speaker.say(f"Could not find {key} anywhere on this system.")
                return

        # Handle .url shortcut files (Steam / Epic browser protocol links)
        if path.lower().endswith(".url"):
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
            print(f"  [LAUNCH] {key} via .url shortcut")
            return

        # Handle .lnk Windows shortcut files
        if path.lower().endswith(".lnk"):
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
            print(f"  [LAUNCH] {key} via .lnk shortcut")
            return

        try:
            proc = subprocess.Popen([path] + flags)
            print(f"  [LAUNCH] {key} — PID {proc.pid}")
            self.failures.record_success(key, path)
            self.usage.record(key, success=True)
        except FileNotFoundError:
            self.failures.record_failure(key, path)
            self.usage.record(key, success=False)
            self.speaker.say(f"Launch failed for {key}. Path not found.")
            return
        except Exception as launch_err:
            self.failures.record_failure(key, path)
            self.usage.record(key, success=False)
            self.speaker.say(f"Launch failed for {key}: {launch_err}")
            return

        if priority and PSUTIL_AVAILABLE:
            time.sleep(2)
            try:
                p = psutil.Process(proc.pid)
                priority_map = {
                    "high":         psutil.HIGH_PRIORITY_CLASS,
                    "above_normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                    "normal":       psutil.NORMAL_PRIORITY_CLASS,
                }
                p.nice(priority_map.get(priority, psutil.NORMAL_PRIORITY_CLASS))
                print(f"  [PRIORITY] Set to {priority}")
            except Exception as e:
                print(f"  [WARN] Priority set failed: {e}")

    def _set_volume_raw(self, level_float: float):
        """Set volume immediately (0.0–1.0). Internal helper."""
        if PYCAW_AVAILABLE:
            try:
                devices  = AudioUtilities.GetSpeakers()
                iface    = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                vol_ctrl = cast(iface, POINTER(IAudioEndpointVolume))
                vol_ctrl.SetMasterVolumeLevelScalar(level_float, None)
                return True
            except Exception:
                pass
        nircmd = self.config.get("tools", {}).get("nircmd", "nircmd")
        result = subprocess.run(
            [nircmd, "setsysvolume", str(int(level_float * 65535))],
            capture_output=True
        )
        return result.returncode == 0

    def _get_volume_raw(self) -> float:
        """Get current volume (0.0–1.0). Internal helper."""
        if PYCAW_AVAILABLE:
            try:
                devices  = AudioUtilities.GetSpeakers()
                iface    = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                vol_ctrl = cast(iface, POINTER(IAudioEndpointVolume))
                return vol_ctrl.GetMasterVolumeLevelScalar()
            except Exception:
                pass
        return 0.5

    def _volume(self, action: dict):
        target    = max(0, min(100, int(action.get("level", 50))))
        fade      = action.get("fade", True)
        steps     = 20
        duration  = 1.0  # seconds

        if not fade:
            ok = self._set_volume_raw(target / 100.0)
            if ok:
                print(f"  [VOLUME] Set to {target}%")
            else:
                self.speaker.say("Volume control unavailable.")
            return

        # Smooth fade
        current = self._get_volume_raw() * 100
        if abs(current - target) < 2:
            return  # already there

        def _fade():
            step_size = (target - current) / steps
            step_time = duration / steps
            for i in range(steps):
                new_level = current + step_size * (i + 1)
                self._set_volume_raw(max(0, min(100, new_level)) / 100.0)
                time.sleep(step_time)
            self._set_volume_raw(target / 100.0)
            print(f"  [VOLUME] Faded to {target}%")

        import threading
        threading.Thread(target=_fade, daemon=True).start()

    def _url(self, action: dict):
        url = action.get("url", "")
        if not url:
            return
        browser_path = self.config.get("tools", {}).get("browser", None)
        if browser_path and os.path.exists(browser_path):
            subprocess.Popen([browser_path, "--profile-directory=Default", url])
        else:
            webbrowser.open(url)
        print(f"  [URL] Opened: {url}")

    def _search(self, action: dict):
        query = action.get("query", "")
        if not query:
            return
        encoded = query.replace(" ", "+")
        self._url({"url": f"https://www.google.com/search?q={encoded}"})
        print(f"  [SEARCH] Query: {query}")

    def _kill(self, action: dict):
        process = action.get("process", "")
        name    = action.get("name", process)
        if not process:
            return

        if PSUTIL_AVAILABLE:
            killed = 0
            for proc in psutil.process_iter(["pid", "name"]):
                if process.lower() in proc.info["name"].lower():
                    try:
                        proc.kill()
                        killed += 1
                        print(f"  [KILL] {proc.info['name']} (PID {proc.info['pid']})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        print(f"  [WARN] Kill failed: {e}")
            if killed == 0:
                self.speaker.say(f"{name} not found in process list.")
        else:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", process],
                capture_output=True, text=True
            )
            print(f"  [KILL] taskkill {process}: {result.stdout.strip()}")

    def _power(self, action: dict):
        command = action.get("command", "").lower()
        cmds = {
            "sleep":    ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            "restart":  ["shutdown", "/r", "/t", "5"],
            "shutdown": ["shutdown", "/s", "/t", "5"],
        }
        if command in cmds:
            subprocess.Popen(cmds[command])
            print(f"  [POWER] {command.upper()} initiated")
        else:
            self.speaker.say(f"Unknown power command: {command}")

    def _thermal(self, _action: dict):
        report = []

        if PSUTIL_AVAILABLE:
            cpu_pct = psutil.cpu_percent(interval=1)
            report.append(f"CPU load: {cpu_pct}%")

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) == 2:
                    report.append(f"GPU temp: {parts[0]}C  GPU load: {parts[1]}%")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        msg = ". ".join(report) if report else "Thermal data unavailable."
        print(f"  [THERMAL] {msg}")
        self.speaker.say(msg)

    def _macro(self, action: dict):
        name   = action.get("name", "").lower()
        macros = self.config.get("macros", {})

        if name not in macros:
            self.speaker.say(f"Macro '{name}' not found.")
            return

        actions = macros[name].get("actions", [])
        print(f"  [MACRO] Executing: {name} ({len(actions)} actions)")

        for sub_action in actions:
            delay = sub_action.pop("delay", 0)
            if delay:
                time.sleep(delay)
            self.execute(sub_action)

    def _speak(self, action: dict):
        text = action.get("text", "")
        if text:
            self.speaker.say(text)

    def _vision(self, action: dict):
        """Capture screen and describe or answer a question about it."""
        if not VISION_AVAILABLE:
            self.speaker.say("Vision module not available. Install mss and pillow.")
            return
        question = action.get("question", "")
        monitor  = action.get("monitor", 0)
        print(f"  [VISION] Capturing monitor {monitor}...")
        if question:
            result = analyse_screen(question, monitor_index=monitor)
        else:
            result = describe_screen(monitor_index=monitor)
        print(f"  [VISION] {result}")
        self.speaker.say(result)

    def _food(self, action: dict):
        """
        Open the restaurant's own ordering website directly.
        Navigates as deep as possible (category/item page), then hands off.
        """
        restaurant = action.get("restaurant", "").strip()
        item       = action.get("item", "").strip() or None
        order_type = action.get("order_type", "order").lower()

        if not restaurant:
            self.speaker.say("Which restaurant would you like to order from, Sir?")
            return

        if not FOOD_AVAILABLE:
            import webbrowser
            url = f"https://www.google.com/search?q={restaurant.replace(' ', '+')}+order+online"
            webbrowser.open(url)
            self.speaker.say(f"Searched for {restaurant} online ordering, Sir.")
            return

        print(f"  [FOOD] Restaurant: {restaurant} | Item: {item} | Type: {order_type}")

        if order_type in ("reservation", "reserve", "book", "table"):
            msg = find_reservation(restaurant)
        else:
            msg = order_food(restaurant, item)

        print(f"  [FOOD] {msg}")
        self.speaker.say(msg)

    def _window(self, action: dict):
        """Window management — snap, focus, tile, etc."""
        if not WINDOW_MANAGER_AVAILABLE:
            self.speaker.say("Window management not available. Run: pip install pygetwindow pywin32")
            return
        msg = dispatch_window_action(action)
        print(f"  [WINDOW] {msg}")
        self.speaker.say(msg)

    def _reminder(self, action: dict):
        """Set a timed reminder via the notification system."""
        time_str = action.get("time", "")
        message  = action.get("message", "Reminder, Sir.")
        repeat   = action.get("repeat", False)
        if hasattr(self, "notifications") and self.notifications:
            self.notifications.add_reminder(time_str, message, repeat)
            self.speaker.say(
                f"Reminder set for {time_str}, Sir." if time_str
                else "Reminder noted, Sir."
            )
        else:
            self.speaker.say("Reminder system not active, Sir.")