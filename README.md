# CORE NEXUS — Setup & Usage

```
╔══════════════════════════════════════════════╗
║          CORE NEXUS — v1.0                   ║
║   Personal Digital Concierge / OS Bridge     ║
╚══════════════════════════════════════════════╝
```

## Architecture

```
You speak → Python listener detects "Nexus" →
Command sent to Claude API (with your config as context) →
Claude returns structured JSON action plan →
executor.py dispatches OS-level actions
```

---

## 1. Prerequisites

- Python 3.10+
- An Anthropic API key → https://console.anthropic.com

---

## 2. Setup

**Option A — Batch (easiest):**
```
Double-click setup.bat
```

**Option B — Manual:**
```powershell
pip install -r requirements.txt
```

**PyAudio note** — sometimes fails on Windows. Fix:
```powershell
pip install pipwin
pipwin install pyaudio
```

---

## 3. Set Your API Key

**Temporary (current session only):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Permanent (recommended):**
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")
```
Then restart your terminal.

---

## 4. Configure Your Apps — `config.json`

Edit `config.json` and fill in real paths:

```json
"trackmania": {
    "path": "F:\\Games\\Trackmania\\TmForever.exe",
    "priority": "high"
}
```

Update the `study_mode` macro URL to your school portal.

---

## 5. Launch

**Voice mode:**
```powershell
python core_nexus.py
```

**Text mode (for testing — no mic needed):**
```powershell
python core_nexus.py --text
```

**PowerShell launcher (with admin option):**
```powershell
.\launch_nexus.ps1              # normal
.\launch_nexus.ps1 -TextMode    # text input
.\launch_nexus.ps1 -AsAdmin     # elevated (needed for priority control)
```

---

## 6. Usage

Say **"Nexus"** followed by your command:

| Voice Command | What Happens |
|---|---|
| `Nexus, launch Trackmania` | Launches Trackmania at high priority |
| `Nexus, set volume to 50` | System volume → 50% |
| `Nexus, study mode` | Kills games/Discord, opens school portal |
| `Nexus, game mode` | Kills Chrome, launches Discord |
| `Nexus, search current Trackmania world records` | Opens Google search |
| `Nexus, kill Discord` | Asks confirmation, then kills Discord.exe |
| `Nexus, restart` | Asks confirmation, then restarts PC in 5s |
| `Nexus, thermals` | Reports CPU load + GPU temp |
| `Nexus, open youtube` | Opens youtube.com in browser |

---

## 7. Adding New Apps

In `config.json` under `"apps"`:
```json
"valorant": {
    "path": "F:\\Riot Games\\VALORANT\\live\\VALORANT.exe",
    "description": "Valorant",
    "priority": "high",
    "flags": []
}
```

---

## 8. Adding New Macros

In `config.json` under `"macros"`:
```json
"stream_mode": {
    "description": "Launch OBS and Discord, set volume to 40",
    "actions": [
        { "type": "launch", "key": "obs"      },
        { "type": "launch", "key": "discord"  },
        { "type": "volume", "level": 40        }
    ]
}
```

---

## 9. Volume Control — Fallback Chain

1. **pycaw** (primary) — pure Python, works on most Windows systems
2. **nircmd** (fallback) — place `nircmd.exe` in `C:\Tools\nircmd\` and update `config.json`  
   Download: https://www.nirsoft.net/utils/nircmd.html

---

## 10. File Structure

```
core_nexus/
├── core_nexus.py     ← Main loop, voice listener, Claude API bridge
├── executor.py       ← OS-level action dispatcher
├── config.json       ← Your apps, macros, and tool paths
├── requirements.txt  ← Python dependencies
├── setup.bat         ← One-click setup
├── launch_nexus.ps1  ← PowerShell launcher
└── README.md
```
