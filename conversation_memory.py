"""
conversation_memory.py — Core Nexus Conversation Memory
Persists conversation history to disk, loads on startup.
Keeps last N exchanges in Ollama context for continuity.
"""

import os
import json
import time
from datetime import datetime

MEMORY_PATH     = os.path.join(os.path.dirname(__file__), "conversation_history.json")
MAX_HISTORY     = 50   # max exchanges to persist to disk
CONTEXT_WINDOW  = 8    # how many recent exchanges to send to Ollama each time


class ConversationMemory:
    def __init__(self):
        self.history: list[dict] = []   # [{role, content, timestamp}]
        self._load()

    def _load(self):
        if os.path.exists(MEMORY_PATH):
            try:
                with open(MEMORY_PATH) as f:
                    data = json.load(f)
                self.history = data.get("history", [])
                print(f"  [MEMORY] Loaded {len(self.history)} past exchanges.")
            except Exception as e:
                print(f"  [MEMORY] Could not load history: {e}")
                self.history = []

    def _save(self):
        try:
            # Keep only last MAX_HISTORY
            trimmed = self.history[-MAX_HISTORY:]
            with open(MEMORY_PATH, "w") as f:
                json.dump({
                    "saved_at": datetime.now().isoformat(),
                    "history":  trimmed
                }, f, indent=2)
        except Exception as e:
            print(f"  [MEMORY] Could not save history: {e}")

    def add(self, role: str, content: str):
        """Add a message. role = 'user' or 'assistant'."""
        self.history.append({
            "role":      role,
            "content":   content,
            "timestamp": time.time()
        })
        self._save()

    def get_context_messages(self) -> list[dict]:
        """
        Return last CONTEXT_WINDOW exchanges in Ollama message format.
        Strips timestamps — Ollama only wants role + content.
        """
        recent = self.history[-(CONTEXT_WINDOW * 2):]  # user+assistant pairs
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    def summarise_recent(self) -> str:
        """
        One-line summary of last few interactions for the system prompt context.
        Helps the model understand recent patterns without blowing the context window.
        """
        if not self.history:
            return "No prior conversation this session."
        recent = self.history[-6:]
        lines  = []
        for m in recent:
            ts  = datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M")
            snip = m["content"][:80].replace("\n", " ")
            lines.append(f"  [{ts}] {m['role'].upper()}: {snip}")
        return "\n".join(lines)

    def clear(self):
        self.history = []
        self._save()
        print("  [MEMORY] History cleared.")
