"""
notifications.py — Core Nexus Background Notification System
Monitors system resources and fires proactive alerts via the speaker.
Runs in a background thread — never blocks the main loop.

Monitors:
  - CPU usage (alert if > threshold for sustained period)
  - GPU temperature (alert if dangerously hot)
  - Session time (remind user to take breaks)
  - Custom scheduled reminders
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta

NOTIF_LOG_PATH = os.path.join(os.path.dirname(__file__), "notifications_log.json")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import subprocess


class NotificationSystem:
    def __init__(self, speaker, socketio=None):
        """
        speaker  : any object with a .say(text) method
        socketio : optional Flask-SocketIO instance for web UI alerts
        """
        self.speaker       = speaker
        self.socketio      = socketio
        self._running      = False
        self._thread       = None
        self._start_time   = time.time()
        self._last_break   = time.time()
        self._log          = []
        self._reminders    = []   # [{time: HH:MM, message: str, repeat: bool}]
        self._fired_today  = set()

        # Thresholds
        self.cpu_threshold      = 90    # % — alert if CPU above this
        self.cpu_sustained_secs = 120   # seconds CPU must be high before alerting
        self.gpu_temp_threshold = 85    # °C — alert if GPU above this
        self.break_interval_min = 120   # minutes between break reminders

        # State tracking
        self._cpu_high_since  = None
        self._last_gpu_alert  = 0
        self._last_cpu_alert  = 0

    def start(self):
        """Start background monitoring thread."""
        self._running = True
        self._thread  = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("  [NOTIF] Background monitoring active.")

    def stop(self):
        self._running = False

    def add_reminder(self, time_str: str, message: str, repeat: bool = True):
        """
        Schedule a reminder.
        time_str: "HH:MM" format
        repeat:   True = fires every day, False = fires once
        """
        self._reminders.append({
            "time":    time_str,
            "message": message,
            "repeat":  repeat
        })
        print(f"  [NOTIF] Reminder set: '{message}' at {time_str}")

    def notify(self, message: str, category: str = "info"):
        """Fire a notification — speaks it and logs it."""
        print(f"  [NOTIF] {category.upper()}: {message}")
        self.speaker.say(message)
        entry = {
            "time":     datetime.now().isoformat(),
            "category": category,
            "message":  message
        }
        self._log.append(entry)
        # Keep log to last 100 entries
        if len(self._log) > 100:
            self._log = self._log[-100:]
        # Emit to web UI if available
        if self.socketio:
            try:
                self.socketio.emit("notification", entry)
            except Exception:
                pass
        self._save_log()

    def get_recent(self, n: int = 10) -> list:
        return self._log[-n:]

    def _save_log(self):
        try:
            with open(NOTIF_LOG_PATH, "w") as f:
                json.dump(self._log, f, indent=2)
        except Exception:
            pass

    def _get_gpu_temp(self) -> int | None:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return None

    def _monitor_loop(self):
        """Main monitoring loop — checks every 30 seconds."""
        while self._running:
            try:
                now = time.time()

                # ── CPU check ─────────────────────────────────────────────────
                if PSUTIL_AVAILABLE:
                    cpu = psutil.cpu_percent(interval=1)
                    if cpu >= self.cpu_threshold:
                        if self._cpu_high_since is None:
                            self._cpu_high_since = now
                        elif (now - self._cpu_high_since >= self.cpu_sustained_secs and
                              now - self._last_cpu_alert > 300):
                            self.notify(
                                f"Sir, CPU has been at {cpu:.0f}% for over "
                                f"{int(self.cpu_sustained_secs/60)} minutes. "
                                f"You may want to close some applications.",
                                "warning"
                            )
                            self._last_cpu_alert = now
                    else:
                        self._cpu_high_since = None

                # ── GPU temperature check ──────────────────────────────────────
                gpu_temp = self._get_gpu_temp()
                if gpu_temp and gpu_temp >= self.gpu_temp_threshold:
                    if now - self._last_gpu_alert > 300:
                        self.notify(
                            f"Warning, Sir. GPU temperature is {gpu_temp}°C. "
                            f"Consider improving airflow or reducing workload.",
                            "warning"
                        )
                        self._last_gpu_alert = now

                # ── Break reminder ─────────────────────────────────────────────
                mins_since_break = (now - self._last_break) / 60
                if mins_since_break >= self.break_interval_min:
                    self.notify(
                        f"Sir, you have been at your desk for "
                        f"{int(mins_since_break)} minutes. "
                        f"Perhaps a short break is in order.",
                        "reminder"
                    )
                    self._last_break = now

                # ── Scheduled reminders ────────────────────────────────────────
                current_time = datetime.now().strftime("%H:%M")
                for reminder in self._reminders:
                    key = f"{reminder['time']}_{reminder['message']}"
                    if (current_time == reminder["time"] and
                            key not in self._fired_today):
                        self.notify(reminder["message"], "reminder")
                        self._fired_today.add(key)
                        if not reminder["repeat"]:
                            self._reminders.remove(reminder)

                # Reset fired_today at midnight
                if current_time == "00:00":
                    self._fired_today.clear()

            except Exception as e:
                print(f"  [NOTIF] Monitor error: {e}")

            time.sleep(30)
