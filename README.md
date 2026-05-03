# CORE NEXUS — Setup Guide
### (Written so anyone can follow along!)

```
╔══════════════════════════════════════════════╗
║          CORE NEXUS — v2.0                   ║
║   Your Personal AI Butler for your PC        ║
╚══════════════════════════════════════════════╝
```

---

## What is Core Nexus?

Imagine having a butler who lives inside your computer — inspired by Jarvis from Iron Man.
You say **"Nexus"** (or just **"Nexus"** in text mode), tell it what you want, and it does it.

- *"Nexus, open Minecraft"* → Minecraft launches automatically
- *"Nexus, set volume to 50"* → Volume changes to 50%
- *"Nexus, order me a pizza from Dominos"* → Dominos opens ready to order
- *"Nexus, what's on my screen?"* → AI reads and describes your screen
- *"Nexus, snap Discord to the left"* → Window snaps to left half
- *"Nexus, remind me at 6pm to eat"* → Sets a timed reminder

The AI brain runs **100% on your own computer** — no cloud, no subscription, no API key.
It uses your GPU to think, just like it does for games.

---

## Before You Start — What You'll Need

- A Windows PC (Windows 10 or 11)
- An internet connection (just for setup — Nexus runs offline after)
- A microphone (built-in or USB both work)
- An NVIDIA GPU with at least 4GB VRAM (GTX 1060 or better)

> No good GPU? It still works, just slower — responses take ~20 seconds instead of ~2.

---

## File Structure

```
F:\Projects\ai\
├── launcher.pyw            ← Double-click to start everything (HUD GUI)
├── create_shortcut.bat     ← Run once to create a desktop shortcut
├── core_nexus.py           ← Main voice loop and Ollama AI bridge
├── nexus_server.py         ← Web dashboard server (localhost:8080)
├── executor.py             ← OS action dispatcher
├── app_scanner.py          ← Startup drive scanner, builds app index
├── fuzzy_match.py          ← Speech error correction and failure tracking
├── conversation_memory.py  ← Persistent conversation history
├── screen_vision.py        ← Screenshot + AI vision
├── food_ordering.py        ← Restaurant website navigation
├── notifications.py        ← Background CPU/GPU monitor and reminders
├── wake_word.py            ← Offline wake word detection (Hey Jarvis)
├── tts_piper.py            ← Neural British voice (Piper TTS)
├── window_manager.py       ← Window snap, focus, tile
├── usage_tracker.py        ← App launch statistics
├── config.json             ← App registry and macros
├── requirements.txt        ← Python dependencies
├── setup.bat               ← One-click dependency installer
├── launch_nexus.ps1        ← PowerShell launcher (alternative)
└── nexus_ui\index.html     ← Jarvis HUD web dashboard
```

---

## STEP 1 — Install Python

Download and install **Python 3.12** from https://www.python.org/downloads/

> **Critical:** During install, tick **"Add Python to PATH"** before clicking Install.

Check it worked — open PowerShell and type:
```powershell
python --version
# Should show: Python 3.12.x
```

---

## STEP 2 — Install Ollama

Ollama is the program that runs the AI brain locally on your GPU.

1. Go to 👉 **https://ollama.com** and click Download
2. Run the installer
3. Open PowerShell and pull the AI model:

```powershell
ollama pull gemma3:4b
```

This downloads about **3GB** — like downloading a game. Wait for it to finish.

Check it worked:
```powershell
ollama list
# Should show: gemma3:4b
```

> Every time you use Nexus, Ollama needs to be running. It usually starts automatically.
> If Nexus says "Ollama is not running", click **Start Ollama** in the launcher.

---

## STEP 3 — Copy the Project Files

Place all project files into:
```
F:\Projects\ai\
```

You can use a different path — just be consistent throughout.

---

## STEP 4 — Run Automatic Setup

This does everything for you — installs dependencies, detects your apps, builds
a personalised `config.json`, and creates a desktop shortcut:

```powershell
cd F:\Projects\ai
python setup_nexus.py
```

That's it. The script will:
- Install all Python packages automatically
- Start Ollama and download the AI model
- Scan your PC for installed apps and build `config.json` for **your** system
- Set the PowerShell execution policy
- Create a **Core Nexus** shortcut on your Desktop

> The config is built specifically for whoever runs this script — no manual path editing needed.

---

## STEP 8 — Launch

**Option A — Desktop shortcut (easiest after setup):**
```
Double-click "Core Nexus" on your desktop
```

**Option B — Direct launch:**
```powershell
cd F:\Projects\ai
& "C:\Users\lukes\AppData\Local\Programs\Python\Python312\pythonw.exe" launcher.pyw
```

**Option C — Text mode (no microphone, good for testing):**
```powershell
python core_nexus.py --text
```

**Option D — Web UI only:**
```powershell
python nexus_server.py
# Then open: http://localhost:8080
```

---

## STEP 9 — First Boot

On first launch, Nexus scans all your drives to build an app index.
This takes **15–60 seconds** and you'll see:

```
[SCAN] Building app cache across all drives...
[SCAN] Drive C:\ ... 469 apps found
[SCAN] Drive F:\ ... 168 apps found
[SCAN] Cache saved: 896 apps
[OK] App index ready!
```

Every launch after that loads from cache instantly. It rescans every 24 hours automatically.

The launcher shows a **Jarvis HUD** with animated rotating rings and a pulsing arc reactor.
Click **▶ LAUNCH NEXUS** to start both the voice engine and web dashboard together.

---

## Usage — Voice Commands

Say **"Nexus"** followed by your command:

| Say This | What Happens |
|---|---|
| `Nexus, open Discord` | Launches Discord |
| `Nexus, open Minecraft` | Launches Minecraft |
| `Nexus, set volume to 30` | Sets volume to 30% |
| `Nexus, what's on my screen` | AI describes your screen |
| `Nexus, thermals` | Reports CPU load and GPU temperature |
| `Nexus, order pizza from Dominos` | Opens Dominos ordering page |
| `Nexus, book a table at Swiss Chalet` | Opens OpenTable |
| `Nexus, snap Discord to the left` | Snaps Discord window left |
| `Nexus, tile Discord and Chrome` | Tiles two windows side by side |
| `Nexus, open YouTube` | Opens YouTube in browser |
| `Nexus, search Trackmania world records` | Google search |
| `Nexus, kill Discord` | Asks confirmation then closes Discord |
| `Nexus, sleep` | Puts PC to sleep |
| `Nexus, restart` | Asks confirmation then restarts in 5s |
| `Nexus, game mode` | Closes Chrome, opens Discord, sets volume 60 |
| `Nexus, study mode` | Closes games and Discord, opens school portal |
| `Nexus, remind me at 6pm to eat` | Sets a 6pm reminder |

> **Speech errors are handled automatically.** Saying "rinecraft" opens Minecraft.
> Saying "geo dash" opens Geometry Dash. "fort night" opens Fortnite.

---

## The Web Dashboard

Open **http://localhost:8080** (or click **Open Dashboard** in the launcher).

The Jarvis HUD dashboard shows:
- Animated arc reactor in the centre
- Live CPU and GPU stats
- Activity log of everything Nexus says and does
- Top applications by launch count
- Notification feed (CPU/GPU alerts, reminders)
- Command input box at the bottom

---

## Supported Food Ordering

Say *"Hey Jarvis, order [food] from [restaurant]"* and Nexus opens that restaurant's
own ordering website directly on the menu/order page. You complete checkout yourself.

Supported restaurants: **Domino's · KFC · Subway · McDonald's · Burger King · Pizza Hut ·
Wendy's · Taco Bell · Popeyes · A&W · Harvey's · Swiss Chalet · Starbucks ·
Tim Hortons · Boston Pizza**

For reservations: *"Hey Jarvis, book a table at [restaurant]"* opens OpenTable.

To add more restaurants, open `food_ordering.py` and add an entry to the `RESTAURANTS` dict.

---

## Adding Your Own Apps

In `config.json` under `"apps"`:
```json
"valorant": {
    "path": "C:\\Riot Games\\VALORANT\\live\\VALORANT.exe",
    "description": "Valorant",
    "priority": "high",
    "flags": []
}
```

Or just say *"Hey Jarvis, open [app name]"* — if the app is installed anywhere on your
drives, Nexus will find it automatically and remember the path for next time.

---

## Adding Your Own Macros

Macros let you chain multiple actions into one voice command.
Add them to `config.json` under `"macros"`:

```json
"stream mode": {
    "description": "Get ready to stream",
    "actions": [
        { "type": "launch", "key": "obs"     },
        { "type": "launch", "key": "discord" },
        { "type": "volume", "level": 40      },
        { "type": "speak",  "text": "Stream mode active." }
    ]
}
```

Then say *"Hey Jarvis, stream mode"* and all four things happen at once.

---

## Custom Wake Word

By default Nexus responds to **"Nexus"** — which fits the Iron Man theme.

To change it, update `config.json`:
```json
"wake_keyword": "alexa"
```

Available built-in options: `hey_jarvis`, `alexa`, `hey_mycroft`, `hey_rhasspy`

To train a custom **"Nexus"** wake word:
1. Go to https://openwakeword.com
2. Train a model for the word "Nexus"
3. Download the `.tflite` file
4. Save it as `F:\Projects\ai\nexus_wakeword.tflite`
5. Nexus will pick it up automatically on next launch

---

## Troubleshooting

**Launcher opens but nothing starts**
Make sure you're using the shortcut created by `create_shortcut.bat` — it points to
the correct Python 3.12. If clicking the launcher directly, run it via PowerShell:
```powershell
& "C:\Users\lukes\AppData\Local\Programs\Python\Python312\pythonw.exe" "F:\Projects\ai\launcher.pyw"
```

**"Ollama is not running"**
```powershell
ollama serve
```
Keep that window open, then relaunch Nexus.

**Nexus can't hear you**
Go to Windows Settings → System → Sound → set your mic as the default input device.
Test without mic: `python core_nexus.py --text`

**App won't open / wrong app launches**
Add it manually to `config.json`. For Steam games use `steam://rungameid/APPID`.
For desktop shortcuts point to the `.url` or `.lnk` file directly.

**Force a fresh app scan**
```powershell
python app_scanner.py
```

**PyAudio won't install**
```powershell
pip install pipwin
pipwin install pyaudio
```

**Piper voice not working**
```powershell
pip install soundfile
```

---

## Quick Cheat Sheet

```
Start (GUI):         Double-click "Core Nexus" desktop shortcut
Start (voice only):  python core_nexus.py
Start (web UI only): python nexus_server.py
Start (no mic):      python core_nexus.py --text
Re-scan drives:      python app_scanner.py
Start Ollama:        ollama serve
```

---

## Hardware Recommendations

| Component | Minimum | Recommended |
|---|---|---|
| GPU | NVIDIA GTX 1060 6GB | NVIDIA RTX 3070+ |
| RAM | 8GB | 16GB+ |
| OS | Windows 10 | Windows 11 |
| Mic | Any USB/3.5mm | Dedicated USB mic |

---

*Built with Python · Powered by Ollama + gemma3:4b · Runs 100% locally*
*Inspired by Jarvis from Iron Man*
