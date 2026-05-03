"""
usage_tracker.py — Core Nexus App Usage Statistics
Records every app launch with timestamp.
Provides stats for the web dashboard.
"""

import os
import json
import time
from datetime import datetime, timedelta
from collections import Counter

USAGE_PATH = os.path.join(os.path.dirname(__file__), "usage_stats.json")


class UsageTracker:
    def __init__(self):
        self._data = []
        self._load()

    def _load(self):
        if os.path.exists(USAGE_PATH):
            try:
                with open(USAGE_PATH) as f:
                    self._data = json.load(f)
            except Exception:
                self._data = []

    def _save(self):
        try:
            # Keep last 1000 entries
            trimmed = self._data[-1000:]
            with open(USAGE_PATH, "w") as f:
                json.dump(trimmed, f)
            self._data = trimmed
        except Exception:
            pass

    def record(self, app_name: str, success: bool = True):
        """Record a launch attempt."""
        self._data.append({
            "app":       app_name,
            "time":      time.time(),
            "timestamp": datetime.now().isoformat(),
            "success":   success
        })
        self._save()

    def top_apps(self, n: int = 10, days: int = 7) -> list[dict]:
        """Return the N most launched apps in the last N days."""
        cutoff = time.time() - (days * 86400)
        recent = [d for d in self._data if d["time"] >= cutoff and d.get("success")]
        counts = Counter(d["app"] for d in recent)
        return [{"app": app, "count": count} for app, count in counts.most_common(n)]

    def recent_launches(self, n: int = 20) -> list[dict]:
        """Return the N most recent launches."""
        return list(reversed(self._data[-n:]))

    def today_count(self) -> int:
        """How many launches today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
        return sum(1 for d in self._data if d["time"] >= today_start)

    def total_count(self) -> int:
        return len(self._data)

    def get_summary(self) -> dict:
        return {
            "total":       self.total_count(),
            "today":       self.today_count(),
            "top_apps":    self.top_apps(10),
            "recent":      self.recent_launches(10),
        }
