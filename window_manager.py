"""
window_manager.py — Core Nexus Window Manager
Snap, resize, focus, and manage application windows.

Setup:
  pip install pygetwindow pywin32

Supports:
  - Snap left / right / maximize / minimize / restore
  - Focus a specific app by name
  - Move window to specific monitor
  - Tile two apps side by side
"""

import os
import time
import subprocess

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False

try:
    import win32gui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def _find_window(name: str):
    """Find a window by partial title match."""
    if not PYGETWINDOW_AVAILABLE:
        return None
    name_lower = name.lower()
    all_windows = gw.getAllWindows()
    for win in all_windows:
        if win.title and name_lower in win.title.lower():
            return win
    return None


def _get_screen_size() -> tuple[int, int]:
    """Get primary monitor resolution."""
    if WIN32_AVAILABLE:
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        return w, h
    return 1920, 1080  # fallback


def snap_left(app_name: str) -> str:
    """Snap a window to the left half of the screen."""
    win = _find_window(app_name)
    if not win:
        return f"Could not find a window for '{app_name}', Sir."
    try:
        sw, sh = _get_screen_size()
        win.restore()
        time.sleep(0.1)
        win.moveTo(0, 0)
        win.resizeTo(sw // 2, sh)
        return f"Snapped {app_name} to the left, Sir."
    except Exception as e:
        return f"Could not snap window: {e}"


def snap_right(app_name: str) -> str:
    """Snap a window to the right half of the screen."""
    win = _find_window(app_name)
    if not win:
        return f"Could not find a window for '{app_name}', Sir."
    try:
        sw, sh = _get_screen_size()
        win.restore()
        time.sleep(0.1)
        win.moveTo(sw // 2, 0)
        win.resizeTo(sw // 2, sh)
        return f"Snapped {app_name} to the right, Sir."
    except Exception as e:
        return f"Could not snap window: {e}"


def maximize_window(app_name: str) -> str:
    """Maximize a window."""
    win = _find_window(app_name)
    if not win:
        return f"Could not find a window for '{app_name}', Sir."
    try:
        win.maximize()
        return f"Maximized {app_name}, Sir."
    except Exception as e:
        return f"Could not maximize: {e}"


def minimize_window(app_name: str) -> str:
    """Minimize a window."""
    win = _find_window(app_name)
    if not win:
        return f"Could not find a window for '{app_name}', Sir."
    try:
        win.minimize()
        return f"Minimized {app_name}, Sir."
    except Exception as e:
        return f"Could not minimize: {e}"


def focus_window(app_name: str) -> str:
    """Bring a window to the foreground."""
    win = _find_window(app_name)
    if not win:
        return f"Could not find a window for '{app_name}', Sir."
    try:
        win.restore()
        win.activate()
        return f"Focused {app_name}, Sir."
    except Exception as e:
        # Fallback using win32
        if WIN32_AVAILABLE:
            try:
                hwnd = win32gui.FindWindow(None, win.title)
                win32gui.SetForegroundWindow(hwnd)
                return f"Focused {app_name}, Sir."
            except Exception:
                pass
        return f"Could not focus window: {e}"


def tile_side_by_side(app1: str, app2: str) -> str:
    """Tile two windows side by side."""
    win1 = _find_window(app1)
    win2 = _find_window(app2)

    missing = []
    if not win1:
        missing.append(app1)
    if not win2:
        missing.append(app2)
    if missing:
        return f"Could not find windows for: {', '.join(missing)}, Sir."

    try:
        sw, sh = _get_screen_size()
        win1.restore()
        win2.restore()
        time.sleep(0.1)
        win1.moveTo(0, 0)
        win1.resizeTo(sw // 2, sh)
        win2.moveTo(sw // 2, 0)
        win2.resizeTo(sw // 2, sh)
        return f"Tiled {app1} and {app2} side by side, Sir."
    except Exception as e:
        return f"Could not tile windows: {e}"


def list_open_windows() -> list[str]:
    """Return titles of all visible windows."""
    if not PYGETWINDOW_AVAILABLE:
        return []
    return [w.title for w in gw.getAllWindows() if w.title.strip()]


def dispatch_window_action(action: dict) -> str:
    """
    Main dispatcher for window actions.
    action format:
    {
        "type":    "window",
        "command": "snap_left|snap_right|maximize|minimize|focus|tile",
        "app":     "app name",
        "app2":    "second app name (for tile only)"
    }
    """
    if not PYGETWINDOW_AVAILABLE:
        return "Window management not available. Run: pip install pygetwindow pywin32"

    command = action.get("command", "").lower()
    app     = action.get("app", "")
    app2    = action.get("app2", "")

    dispatch = {
        "snap_left":  lambda: snap_left(app),
        "snap right": lambda: snap_right(app),
        "snap_right": lambda: snap_right(app),
        "maximize":   lambda: maximize_window(app),
        "minimise":   lambda: minimize_window(app),
        "minimize":   lambda: minimize_window(app),
        "focus":      lambda: focus_window(app),
        "tile":       lambda: tile_side_by_side(app, app2),
    }

    handler = dispatch.get(command)
    if handler:
        return handler()
    return f"Unknown window command: {command}"
