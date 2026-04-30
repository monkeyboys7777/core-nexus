"""
fuzzy_match.py — Core Nexus Fuzzy Matching + Failure Adaptation
Corrects speech recognition errors against known app names.
Tracks failed launches and learns better paths over time.
"""

import os
import json
import difflib
import re

FAILURES_PATH = os.path.join(os.path.dirname(__file__), "launch_failures.json")

# Common phonetic substitutions from speech recognition errors
PHONETIC_FIXES = {
    "rinecraft":   "minecraft",
    "meincraft":   "minecraft",
    "mind craft":  "minecraft",
    "mine craft":  "minecraft",
    "fork nite":   "fortnite",
    "fort night":  "fortnite",
    "fortnigt":    "fortnite",
    "war thunder": "war thunder",
    "warthunder":  "war thunder",
    "geo dash":    "geometry dash",
    "geometry das":"geometry dash",
    "rainbow sex": "rainbow six",     # classic SR error
    "rainbow 6":   "rainbow six",
    "discord":     "discord",
    "disc cord":   "discord",
    "you tube":    "youtube",
    "you-tube":    "youtube",
    "git hub":     "github",
    "git-hub":     "github",
    "v s code":    "vscode",
    "vs code":     "vscode",
    "visual studio code": "vscode",
    "roblocks":    "roblox",
    "row blocks":  "roblox",
    "trackmania":  "trackmania",
    "track mania": "trackmania",
    "stanley pair": "stanley parable",
    "lm studio":   "lm studio",
    "el em studio":"lm studio",
    "obs studio":  "obs",
    "after burner":"msi afterburner",
    "fur mark":    "furmark",
    "fur mark 2":  "furmark 2",
    "steam":       "steam",
    "epic":        "epic games",
    "epic game":   "epic games",
    "battle net":  "battle.net",
    "blizzard":    "battle.net",
    "ubisof":      "ubisoft connect",
    "ubisoft":     "ubisoft connect",
}


def normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def correct_speech(spoken: str, known_keys: list[str]) -> str:
    """
    Attempt to correct a speech-recognised app name.
    Returns the best matching known key, or the original if no good match.
    """
    norm = normalise(spoken)

    # 1. Phonetic fix table
    if norm in PHONETIC_FIXES:
        fixed = PHONETIC_FIXES[norm]
        print(f"  [FUZZY] Phonetic fix: '{spoken}' → '{fixed}'")
        return fixed

    # 2. Exact match in known keys
    if norm in known_keys:
        return norm

    # 3. Substring match
    for key in known_keys:
        if norm in key or key in norm:
            return key

    # 4. difflib fuzzy match (handles 1-2 char transcription errors)
    matches = difflib.get_close_matches(norm, known_keys, n=1, cutoff=0.65)
    if matches:
        print(f"  [FUZZY] Fuzzy match: '{spoken}' → '{matches[0]}'")
        return matches[0]

    # 5. Token sort: split into words, check if most words match a key
    spoken_words = set(norm.split())
    best_score   = 0
    best_key     = None
    for key in known_keys:
        key_words  = set(key.split())
        overlap    = len(spoken_words & key_words)
        if overlap > 0:
            score = overlap / max(len(spoken_words), len(key_words))
            if score > best_score:
                best_score = score
                best_key   = key
    if best_score >= 0.5 and best_key:
        print(f"  [FUZZY] Token match ({best_score:.0%}): '{spoken}' → '{best_key}'")
        return best_key

    # No correction found — return original
    return spoken


# ── Failure tracking ────────────────────────────────────────────────────────────

class FailureTracker:
    def __init__(self):
        self.failures: dict = {}
        self._load()

    def _load(self):
        if os.path.exists(FAILURES_PATH):
            try:
                with open(FAILURES_PATH) as f:
                    self.failures = json.load(f)
            except Exception:
                self.failures = {}

    def _save(self):
        try:
            with open(FAILURES_PATH, "w") as f:
                json.dump(self.failures, f, indent=2)
        except Exception:
            pass

    def record_failure(self, key: str, attempted_path: str):
        """Record a failed launch attempt."""
        if key not in self.failures:
            self.failures[key] = {"count": 0, "failed_paths": [], "resolved_path": None}
        entry = self.failures[key]
        entry["count"] += 1
        if attempted_path and attempted_path not in entry["failed_paths"]:
            entry["failed_paths"].append(attempted_path)
        self._save()
        print(f"  [ADAPT] Recorded failure #{entry['count']} for '{key}'")

    def record_success(self, key: str, working_path: str):
        """Record a successful launch — saves the working path."""
        if key not in self.failures:
            self.failures[key] = {"count": 0, "failed_paths": [], "resolved_path": None}
        self.failures[key]["resolved_path"] = working_path
        self._save()
        print(f"  [ADAPT] Saved working path for '{key}': {working_path}")

    def get_failed_paths(self, key: str) -> list[str]:
        return self.failures.get(key, {}).get("failed_paths", [])

    def get_resolved_path(self, key: str) -> str | None:
        return self.failures.get(key, {}).get("resolved_path", None)

    def failure_count(self, key: str) -> int:
        return self.failures.get(key, {}).get("count", 0)
