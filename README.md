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

Imagine having a butler who lives inside your computer. You say **"Nexus"** out loud,
tell it what you want, and it does it for you. You can say things like:

- *"Nexus, open Minecraft"* → Minecraft launches automatically
- *"Nexus, set volume to 50"* → Volume changes to 50%
- *"Nexus, order me a pizza from Dominos"* → Dominos website opens ready to order
- *"Nexus, what's on my screen?"* → It looks at your screen and tells you what it sees

The cool part? The AI brain runs **on your own computer** — nothing is sent to the internet.
It uses your graphics card (GPU) to think, just like it does for games.

---

## Before You Start — What You'll Need

- A Windows PC (Windows 10 or 11)
- An internet connection (just for setup)
- A microphone (built-in or USB both work)
- An NVIDIA graphics card with at least 4GB of memory (GTX 1060 or better)

> Don't have a good GPU? It still works, just slower. Responses will take about
> 20 seconds instead of 2 seconds.

---

## STEP 1 — Install Python
### (Python is the language Core Nexus is written in)

1. Go to 👉 **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.12"** button
3. Run the file that downloads
4. **IMPORTANT:** Before you click Install, look for a checkbox that says
   **"Add Python to PATH"** — make sure it is **ticked** ✅
5. Click **Install Now** and wait for it to finish

**Check it worked** — open PowerShell (search "PowerShell" in the Start menu) and type:
```powershell
python --version
```
You should see something like `Python 3.12.3`. If you do, Python is installed! ✅

---

## STEP 2 — Install Ollama
### (Ollama is the program that runs the AI brain)

1. Go to 👉 **https://ollama.com**
2. Click **Download** and run the installer
3. Once installed, open PowerShell and type this to download the AI model:

```powershell
ollama pull gemma3:4b
```

This downloads about **3 gigabytes** — like downloading a big game. Wait for it to finish.
You'll see a progress bar. ✅

**Check it worked:**
```powershell
ollama list
```
You should see `gemma3:4b` in the list. ✅

> **Every time you want to use Nexus**, Ollama needs to be running in the background.
> It usually starts automatically. If Nexus ever says "Ollama is not running",
> open PowerShell and type `ollama serve` to start it manually.

---

## STEP 3 — Copy the Project Files
### (Putting all of Nexus's files in the right place)

Create a folder called `ai` inside `F:\Projects\` so the full path is:
```
F:\Projects\ai\
```

> You can use a different drive or folder if you want — just remember where you put it!

Copy **all** of these files into that folder:

```
app_scanner.py
conversation_memory.py
core_nexus.py
executor.py
food_ordering.py
fuzzy_match.py
nexus_server.py
screen_vision.py
config.json
requirements.txt
setup.bat
launch_nexus.ps1
README.md
nexus_ui\  (this is a folder — copy the whole thing)
```

---

## STEP 4 — Unlock PowerShell Scripts
### (Windows blocks scripts by default for safety — we need to allow ours)

Open PowerShell and paste this line, then press Enter:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Type `Y` and press Enter if it asks you to confirm. ✅

You only ever need to do this once.

---

## STEP 5 — Install the Extra Pieces Nexus Needs
### (Like installing apps, but for Python)

In PowerShell, navigate to your project folder:
```powershell
cd F:\Projects\ai
```

Then run this to install everything automatically:
```powershell
pip install -r requirements.txt
pip install mss pillow selenium webdriver-manager
```

You'll see a lot of text scrolling past — that's normal. Wait until it stops. ✅

**If you see an error about PyAudio**, run these two lines:
```powershell
pip install pipwin
pipwin install pyaudio
```

> **What are all these things?**
> Think of them like plug-in accessories. One lets Nexus hear your microphone,
> one lets it control your volume, one lets it take screenshots, one lets it
> open websites automatically, and so on.

---

## STEP 6 — Update config.json With Your Details
### (Telling Nexus where your apps actually live on your computer)

Open `config.json` in any text editor (Notepad works fine).

Find anywhere that says `lukes` and replace it with **your Windows username**.

For example if your username is `jake`, change:
```
C:\Users\lukes\AppData\...
```
to:
```
C:\Users\jake\AppData\...
```

**For your games**, check that the paths point to where you actually installed them.
If a path is wrong, Nexus will search your drives automatically and still find it —
but having the right path makes it faster.

**For Steam games** — these use a special format that tells Steam to launch the game.
You don't need file paths for these, they look like this:
```json
"war thunder": {
    "path": "steam://rungameid/236390"
}
```
The number is the Steam App ID. You can find any game's ID by looking at its
Steam store page URL: `store.steampowered.com/app/[THE NUMBER HERE]`

---

## STEP 7 — Launch Nexus! 🚀

Open PowerShell, go to your project folder, and start it up:
```powershell
cd F:\Projects\ai
python core_nexus.py
```

**What you'll see on first launch:**
```
Scanning for applications...
[SCAN] Drive C:\ ... 469 apps found
[SCAN] Drive F:\ ... 168 apps found
[SCAN] Cache saved: 574 apps
[OK] App index ready!
Microphone ready.
NEXUS > Core Nexus online. Standing by.
```

The first scan takes about 15–60 seconds while Nexus looks through all your drives
to find every app and game you have installed. After that it remembers everything,
so every launch after this one is instant.

Once you see **"Core Nexus online. Standing by."** — you're ready! 🎉

---

## STEP 8 — Try It Out!

Say **"Nexus"** clearly, then your command. Here are some things to try:

| Say This | What Nexus Does |
|---|---|
| `Nexus, open Discord` | Opens Discord |
| `Nexus, launch Minecraft` | Launches Minecraft |
| `Nexus, set volume to 30` | Turns volume down to 30% |
| `Nexus, open YouTube` | Opens YouTube in your browser |
| `Nexus, what's on my screen` | Looks at your screen and describes it |
| `Nexus, thermals` | Tells you your CPU and GPU temperature |
| `Nexus, order pizza from Dominos` | Opens Dominos ordering page |
| `Nexus, game mode` | Closes Chrome, opens Discord, sets volume to 60 |
| `Nexus, sleep` | Puts your PC to sleep |
| `Nexus, restart` | Asks you to confirm, then restarts your PC |

> **Don't worry about saying things perfectly.** Nexus understands speech errors.
> Saying "rinecraft" still opens Minecraft. Saying "geo dash" still opens Geometry Dash.

---

## The Web Dashboard (Optional)
### (A cool visual control panel in your browser)

If you want a visual dashboard instead of just the black terminal window,
open a **second** PowerShell window and run:
```powershell
cd F:\Projects\ai
python nexus_server.py
```

Then open your browser and go to:
```
http://localhost:8080
```

You'll see a dark control panel where you can type commands and see everything
Nexus is doing in real time. Both the voice mode and web UI can run at the same time.

---

## Adding Your Own Apps

If Nexus can't find an app, you can add it manually.
Open `config.json` and add a new entry inside the `"apps"` section like this:

```json
"valorant": {
    "path": "C:\\Riot Games\\VALORANT\\live\\VALORANT.exe",
    "description": "Valorant",
    "priority": "high",
    "flags": []
}
```

The name on the left (like `"valorant"`) is what you'll say to open it.
The `"path"` is where the .exe file lives on your computer.

---

## Adding Your Own Macros
### (A macro is a shortcut that does multiple things at once)

Add these inside the `"macros"` section of `config.json`:

```json
"stream mode": {
    "description": "Get ready to stream",
    "actions": [
        { "type": "launch", "key": "obs"     },
        { "type": "launch", "key": "discord" },
        { "type": "volume", "level": 40      },
        { "type": "speak",  "text": "Stream mode active, Boss." }
    ]
}
```

Then just say `"Nexus, stream mode"` and all of those things happen automatically.

---

## Something Not Working?

**"Ollama is not running"**
Open a new PowerShell window and type:
```powershell
ollama serve
```
Keep that window open, then start Nexus in a different window.

**"Failed to fetch" in the web dashboard**
The web server isn't running. Open a second PowerShell and run:
```powershell
python nexus_server.py
```

**Nexus can't hear you / microphone not working**
Go to Windows Settings → System → Sound → make sure your microphone is set
as the default input device.

Test without a microphone (type commands instead):
```powershell
python core_nexus.py --text
```

**An app won't open / wrong app opens**
Add it manually to `config.json` with the exact path to the .exe file.
For Steam games, use the `steam://rungameid/APPID` format instead of a file path.

**PyAudio failed to install**
```powershell
pip install pipwin
pipwin install pyaudio
```

**Force Nexus to re-scan all your drives**
```powershell
python app_scanner.py
```

---

## Quick Cheat Sheet

```
Start Nexus:         python core_nexus.py
Start web dashboard: python nexus_server.py
Test without mic:    python core_nexus.py --text
Re-scan all drives:  python app_scanner.py
Start Ollama:        ollama serve
```

---

*Built with Python · Powered by Ollama + gemma3:4b · Runs 100% locally*
