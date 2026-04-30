"""
╔══════════════════════════════════════════════╗
║          CORE NEXUS — v1.1 (Ollama)          ║
║   Personal Digital Concierge / OS Bridge     ║
╚══════════════════════════════════════════════╝
Usage:
  python core_nexus.py           — Voice mode (default)
  python core_nexus.py --text    — Text input mode (for testing)
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("[WARN] speech_recognition not installed. Use --text mode.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARN] pyttsx3 not installed. TTS disabled.")

from executor import ActionExecutor, _APP_CACHE
from app_scanner import build_cache
from conversation_memory import ConversationMemory

WAKE_WORD    = "nexus"
CONFIG_PATH  = os.path.join(os.path.dirname(__file__), "config.json")
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:4b"
BANNER = """
╔══════════════════════════════════════════════╗
║          CORE NEXUS — ONLINE                 ║
║   AI Engine: Ollama / gemma3:4b (local)      ║
║   Awaiting wake-phrase: "Nexus"              ║
╚══════════════════════════════════════════════╝"""


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] config.json not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def build_system_prompt(config: dict) -> str:
    apps   = config.get("apps", {})
    macros = config.get("macros", {})

    apps_block = "\n".join(
        f"  [{key}] -> {data['path']}  ({data.get('description', '')})"
        for key, data in apps.items()
    )
    macros_block = "\n".join(
        f"  [{key}] -> {data.get('description', '')}"
        for key, data in macros.items()
    )

    return f"""ROLE:
You are Core Nexus, an elite AI system administrator and personal concierge. Your persona is calm, sophisticated, and British — formal, precise, with dry wit. You address the user exclusively as "Sir" or "Boss". You execute commands efficiently and decisively within strictly defined system boundaries. You never hallucinate capabilities, never claim to have performed actions you cannot execute, and never bypass security protocols.

INSTRUCTIONS:
1. Execute commands according to established priority hierarchies
2. Mandatory confirmation gates for: kill, shutdown, restart — no exceptions
3. Respect all entries in the REGISTERED APPLICATIONS and MACROS sections below
4. Generate only valid JSON output that exactly matches the defined action schema
5. Never claim to perform actions outside the defined action types
6. Verify the action type exists before including it in the response
7. Never bypass confirmation gates under any circumstances
8. If a command is ambiguous, pick the most conservative interpretation
9. Operate only within the action types and app registry provided
10. speech field must open with "Yes, Sir" or "At once, Boss", then state the action concisely with dry wit

CAPABILITIES (you are limited to exactly these action types — nothing else):
{{"type": "launch", "key": "app_key"}}          — open a registered or discoverable application
{{"type": "volume", "level": 0-100}}             — set system volume
{{"type": "url", "url": "https://..."}}          — open a URL in the browser
{{"type": "search", "query": "terms"}}           — Google search
{{"type": "kill", "process": "name.exe", "name": "label"}}  — terminate a process (REQUIRES CONFIRMATION)
{{"type": "power", "command": "sleep|restart|shutdown"}}    — power management (restart/shutdown REQUIRE CONFIRMATION)
{{"type": "thermal"}}                            — report CPU/GPU temperature and load
{{"type": "macro", "name": "macro_key"}}         — run a defined macro sequence
{{"type": "speak", "text": "message"}}           — speak additional text
{{"type": "vision", "question": "optional specific question", "monitor": 0}}  — see and describe the screen
{{"type": "food", "restaurant": "dominos|kfc|subway|mcdonalds|burger king|pizza hut|wendys|taco bell|etc", "item": "optional item or topping hint", "order_type": "order|reservation"}}  — open restaurant ordering page directly and navigate to item

REGISTERED APPLICATIONS:
{apps_block if apps_block else "  (none configured)"}

REGISTERED MACROS:
{macros_block if macros_block else "  (none configured)"}

CONTEXT:
- Voice-activated system: commands come from speech recognition and may contain minor transcription errors
- Fuzzy-match app names: "geo dash" = "geometry dash", "vs code" = "vscode", "track mania" = "trackmania"
- App keys use the spoken name lowercased (e.g. "geometry dash", "spotify", "obs")
- If an app is not in the registry, still attempt launch using the spoken name as the key — the executor will search the filesystem
- Never substitute a different app than the one requested
- Known sites map: youtube→https://youtube.com, google→https://google.com, reddit→https://reddit.com, twitter→https://twitter.com, twitch→https://twitch.tv, github→https://github.com, netflix→https://netflix.com, discord→https://discord.com, spotify→https://open.spotify.com, gmail→https://mail.google.com, maps→https://maps.google.com, wikipedia→https://wikipedia.org

EXAMPLES:
User: "launch Geometry Dash"
Response: {{"speech": "At once, Boss. Launching Geometry Dash — dodging blocks so you don't have to.", "requires_confirmation": false, "confirmation_prompt": "", "actions": [{{"type": "launch", "key": "geometry dash"}}]}}

User: "kill Discord"
Response: {{"speech": "Yes, Sir. Awaiting your confirmation before terminating Discord.", "requires_confirmation": true, "confirmation_prompt": "Confirm termination of Discord?", "actions": [{{"type": "kill", "process": "Discord.exe", "name": "Discord"}}]}}

User: "set volume to 40"
Response: {{"speech": "Yes, Sir. Volume descending to 40.", "requires_confirmation": false, "confirmation_prompt": "", "actions": [{{"type": "volume", "level": 40}}]}}

User: "open YouTube"
Response: {{"speech": "At once, Sir. Opening YouTube.", "requires_confirmation": false, "confirmation_prompt": "", "actions": [{{"type": "url", "url": "https://youtube.com"}}]}}

User: "order me a pepperoni pizza from Dominos"
Response: {{"speech": "At once, Sir. Opening Domino\'s and navigating to pizza. Complete checkout when ready.", "requires_confirmation": false, "confirmation_prompt": "", "actions": [{{"type": "food", "restaurant": "dominos", "item": "pepperoni pizza", "order_type": "order"}}]}}

User: "book a table at Swiss Chalet"
Response: {{"speech": "Yes, Sir. Opening OpenTable for Swiss Chalet reservations.", "requires_confirmation": false, "confirmation_prompt": "", "actions": [{{"type": "food", "restaurant": "swiss chalet", "item": "", "order_type": "reservation"}}]}}

OBJECTIVES:
1. Execute commands efficiently and without hesitation within defined boundaries
2. Honour all confirmation gates — never skip them regardless of context
3. Generate only valid, schema-compliant JSON — no markdown, no explanation, no extra text
4. Match app names loosely but never substitute a different app
5. Never report success for actions that were not in the defined action schema
6. Maintain the British butler persona in all speech output

Return this exact JSON structure — nothing else:
{{"speech": "Yes, Sir / At once, Boss + concise action statement", "requires_confirmation": false, "confirmation_prompt": "", "actions": []}}"""


class Speaker:
    def __init__(self):
        self.engine = None
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 185)
                voices = self.engine.getProperty("voices")
                for v in voices:
                    if "zira" in v.name.lower() or "david" in v.name.lower():
                        self.engine.setProperty("voice", v.id)
                        break
            except Exception as e:
                print(f"[WARN] TTS init failed: {e}")
                self.engine = None

    def say(self, text: str):
        print(f"  NEXUS > {text}")
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass


class VoiceListener:
    def __init__(self):
        if not VOICE_AVAILABLE:
            raise RuntimeError("speech_recognition not available.")
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        with self.mic as source:
            print("  Calibrating ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = False
            self.recognizer.pause_threshold = 0.5
        print("  Microphone ready.")

    def listen_for_wake(self) -> str | None:
        with self.mic as source:
            try:
                audio      = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                transcript = self.recognizer.recognize_google(audio).lower()
                if WAKE_WORD in transcript:
                    command = transcript.split(WAKE_WORD, 1)[-1].strip(", ")
                    return command if command else "__STANDBY__"
                return None
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"[ERROR] Speech API: {e}")
                return None


class NexusAI:
    def __init__(self, config: dict, memory: "ConversationMemory"):
        self.system_prompt = build_system_prompt(config)
        self.memory        = memory
        try:
            urllib.request.urlopen("http://localhost:11434", timeout=3)
            print("  [OK] Ollama detected.")
        except Exception:
            print("[ERROR] Ollama is not running. Start it with: ollama serve")
            sys.exit(1)

    def interpret(self, command: str) -> dict:
        # Build message list with conversation history for context
        history_msgs = self.memory.get_context_messages() if hasattr(self, "memory") else []
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += history_msgs
        messages += [{"role": "user", "content": command}]

        payload = {
            "model":  OLLAMA_MODEL,
            "stream": False,
            "messages": messages,
            "options": {
                "temperature":    0.3,
                "top_p":          0.9,
                "repeat_penalty": 1.1,
                "num_predict":    512,
            }
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req  = urllib.request.Request(
                OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            raw = result["message"]["content"].strip()

            # Strip markdown fences
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        raw = part
                        break

            # Extract just the JSON object
            start = raw.find("{")
            end   = raw.rfind("}") + 1

            if start == -1 or end <= start:
                print(f"  [DEBUG] Model returned no JSON object. Raw output:\n---\n{raw}\n---")
                return {
                    "speech": "Yes, Sir — though I must confess the model returned gibberish. Standing by.",
                    "requires_confirmation": False,
                    "confirmation_prompt": "",
                    "actions": []
                }

            raw = raw[start:end]
            return json.loads(raw)

        except json.JSONDecodeError:
            print(f"  [DEBUG] Bad JSON: {raw}")
            return {"speech": "Model returned invalid response.", "requires_confirmation": False, "confirmation_prompt": "", "actions": []}
        except urllib.error.URLError as e:
            print(f"  [DEBUG] Ollama error: {e}")
            return {"speech": "Cannot reach Ollama. Is it running?", "requires_confirmation": False, "confirmation_prompt": "", "actions": []}
        except Exception as e:
            print(f"  [DEBUG] Error: {type(e).__name__}: {e}")
            return {"speech": f"Execution failed: {e}", "requires_confirmation": False, "confirmation_prompt": "", "actions": []}


def get_confirmation(prompt: str, speaker: Speaker, text_mode: bool) -> bool:
    speaker.say(prompt + " Say confirm or cancel.")
    if text_mode:
        ans = input("  [CONFIRM] Type 'confirm' or 'cancel': ").strip().lower()
        return ans == "confirm"
    else:
        if not VOICE_AVAILABLE:
            return False
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                ans   = recognizer.recognize_google(audio).lower()
                return "confirm" in ans
            except Exception:
                return False


def main():
    parser = argparse.ArgumentParser(description="Core Nexus")
    parser.add_argument("--text", action="store_true", help="Use text input instead of voice")
    args = parser.parse_args()

    text_mode = args.text or not VOICE_AVAILABLE

    print(BANNER)
    config   = load_config()
    speaker  = Speaker()
    memory   = ConversationMemory()

    # Startup app scan (uses cache if < 24h old)
    print("  Scanning for applications...")
    cache = build_cache()
    _APP_CACHE.update(cache)
    print(f"  [OK] App index ready: {len(_APP_CACHE)} apps.")

    ai       = NexusAI(config, memory)
    executor = ActionExecutor(config, speaker)
    executor.app_cache = _APP_CACHE

    if text_mode:
        print("  [TEXT MODE] Type your command. No wake word needed.\n")
    else:
        try:
            listener = VoiceListener()
        except Exception as e:
            print(f"[ERROR] Voice init failed: {e}\n  Falling back to text mode.")
            text_mode = True
            listener  = None

    speaker.say("Core Nexus online. Standing by.")
    print()

    while True:
        try:
            if text_mode:
                raw = input("  > ").strip()
                if not raw:
                    continue
                command = raw.lower()
                if command in ("exit", "quit"):
                    speaker.say("Core Nexus offline.")
                    break
            else:
                command = listener.listen_for_wake()
                if command is None:
                    continue
                if command == "__STANDBY__":
                    speaker.say("Standing by.")
                    continue
                print(f"  COMMAND > {command}")

            memory.add("user", command)
            print("  Processing...", end="\r")
            plan = ai.interpret(command)

            if plan.get("requires_confirmation"):
                prompt    = plan.get("confirmation_prompt", "Confirm this action?")
                confirmed = get_confirmation(prompt, speaker, text_mode)
                if not confirmed:
                    speaker.say("Action cancelled.")
                    continue

            speech = plan.get("speech", "Executing.")
            speaker.say(speech)
            memory.add("assistant", speech)

            for action in plan.get("actions", []):
                executor.execute(action)

        except KeyboardInterrupt:
            print("\n")
            speaker.say("Core Nexus offline.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            speaker.say(f"Execution failed. Reason: {e}")


if __name__ == "__main__":
    main()