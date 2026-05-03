"""
launcher.pyw — Core Nexus HUD Launcher
Iron Man / Jarvis style GUI. Double-click to start.
"""
import os, sys, time, subprocess, threading, webbrowser, math
import tkinter as tk
from tkinter import font as tkfont

BASE_DIR      = r"F:\Projects\ai"
PYTHON        = r"C:\Users\lukes\AppData\Local\Programs\Python\Python312\python.exe"
VOICE_SCRIPT  = os.path.join(BASE_DIR, "core_nexus.py")
SERVER_SCRIPT = os.path.join(BASE_DIR, "nexus_server.py")
OLLAMA_URL    = "http://localhost:11434"
WEB_UI_URL    = "http://localhost:8080"

# ── Palette
BG      = "#020810"
BG2     = "#040d1a"
BG3     = "#071424"
CYAN    = "#00e5ff"
CYAN2   = "#00b8d4"
CYAN3   = "#84ffff"
DIM     = "#1a4a55"
TEXT    = "#e0f7fa"
TEXT2   = "#4dd0e1"
TEXT3   = "#1a3a45"
RED     = "#ff1744"
GREEN   = "#00e5ff"
YELLOW  = "#ffd600"
W, H    = 520, 620


class HUDLauncher:
    def __init__(self, root):
        self.root        = root
        self.voice_proc  = None
        self.server_proc = None
        self._running    = False
        self._angle      = 0
        self._angle2     = 0
        self._angle3     = 0
        self._pulse      = 0
        self._scan_y     = 0
        self._log_lines  = []

        self._setup_window()
        self._build_ui()
        self._animate()
        self._check_ollama_loop()

    def _setup_window(self):
        self.root.title("Core Nexus")
        self.root.configure(bg=BG)
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - W) // 2
        y = (self.root.winfo_screenheight() - H) // 2
        self.root.geometry(f"{W}x{H}+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try: self.root.iconbitmap(os.path.join(BASE_DIR, "nexus.ico"))
        except: pass

    def _build_ui(self):
        # ── Canvas (top portion: HUD display)
        self.canvas = tk.Canvas(self.root, width=W, height=300,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(fill="x")

        # ── Bottom controls panel
        self.ctrl = tk.Frame(self.root, bg=BG2, height=320)
        self.ctrl.pack(fill="both", expand=True)
        self.ctrl.pack_propagate(False)

        self._build_controls()
        self._draw_static()
        self._create_animated_items()

    def _draw_static(self):
        c = self.canvas
        # Corner brackets
        sz = 18
        opts = dict(fill=CYAN, width=1, tags='static')
        # TL
        c.create_rectangle(0, 0, sz, 1, **opts)
        c.create_rectangle(0, 0, 1, sz, **opts)
        # TR
        c.create_rectangle(W-sz, 0, W, 1, **opts)
        c.create_rectangle(W-1, 0, W, sz, **opts)
        # BL
        c.create_rectangle(0, 299, sz, 300, **opts)
        c.create_rectangle(0, 300-sz, 1, 300, **opts)
        # BR
        c.create_rectangle(W-sz, 299, W, 300, **opts)
        c.create_rectangle(W-1, 300-sz, W, 300, **opts)
        # Header line
        c.create_line(0, 44, W, 44, fill=DIM, width=1, tags='static')
        # Title
        c.create_text(W//2, 22, text="C O R E    N E X U S", tags="static",
                      fill=CYAN, font=("Courier New", 14, "bold"))
        c.create_text(W//2, 38, text="AI CONCIERGE SYSTEM", tags="static",
                      fill=TEXT2, font=("Courier New", 8))

    def _build_controls(self):
        p = self.ctrl

        # Status rows
        sf = tk.Frame(p, bg=BG2)
        sf.pack(fill="x", padx=20, pady=(14,4))

        self._dot_ollama = self._status_row(sf, "OLLAMA AI ENGINE",  "Checking...")
        self._dot_voice  = self._status_row(sf, "VOICE ENGINE",      "Not started")
        self._dot_server = self._status_row(sf, "WEB UI SERVER",     "Not started")

        # Divider
        tk.Frame(p, bg=DIM, height=1).pack(fill="x", padx=0, pady=8)

        # Launch button
        self.launch_btn = tk.Button(
            p, text="▶   LAUNCH NEXUS",
            font=("Courier New", 13, "bold"),
            bg=CYAN, fg=BG, activebackground=CYAN2, activeforeground=BG,
            relief="flat", padx=0, pady=14, cursor="hand2",
            width=28, command=self._toggle,
            bd=0, highlightthickness=0
        )
        self.launch_btn.pack(pady=(4,8))

        # Secondary buttons
        bf = tk.Frame(p, bg=BG2)
        bf.pack()
        self.web_btn = tk.Button(bf, text="Open Dashboard",
            font=("Courier New", 9), bg=BG3, fg=TEXT2,
            activebackground=DIM, relief="flat", padx=14, pady=6,
            cursor="hand2", state="disabled", bd=0, highlightthickness=0,
            command=lambda: webbrowser.open(WEB_UI_URL))
        self.web_btn.pack(side="left", padx=5)
        self.ollama_btn = tk.Button(bf, text="Start Ollama",
            font=("Courier New", 9), bg=BG3, fg=TEXT2,
            activebackground=DIM, relief="flat", padx=14, pady=6,
            cursor="hand2", bd=0, highlightthickness=0,
            command=self._start_ollama)
        self.ollama_btn.pack(side="left", padx=5)

        # Divider
        tk.Frame(p, bg=DIM, height=1).pack(fill="x", pady=(10,0))

        # Log header
        lh = tk.Frame(p, bg=BG2)
        lh.pack(fill="x", padx=20, pady=(5,2))
        tk.Label(lh, text="ACTIVITY LOG", font=("Courier New", 7),
                 bg=BG2, fg=TEXT3).pack(side="left")

        # Log box
        lf = tk.Frame(p, bg=BG, padx=10, pady=4)
        lf.pack(fill="both", expand=True, padx=8, pady=(0,6))
        sb = tk.Scrollbar(lf)
        sb.pack(side="right", fill="y")
        self.log_box = tk.Text(lf, bg=BG, fg=TEXT2, font=("Courier New", 8),
                               relief="flat", state="disabled", wrap="word",
                               yscrollcommand=sb.set, bd=0, highlightthickness=0)
        self.log_box.pack(fill="both", expand=True)
        sb.config(command=self.log_box.yview)
        self.log_box.tag_config("ok",    foreground=CYAN)
        self.log_box.tag_config("err",   foreground=RED)
        self.log_box.tag_config("warn",  foreground=YELLOW)
        self.log_box.tag_config("nexus", foreground=CYAN3)

        # Footer
        tk.Frame(p, bg=DIM, height=1).pack(fill="x")
        tk.Label(p, text="gemma3:4b  ·  Ollama  ·  RTX 3070",
                 font=("Courier New", 7), bg=BG2, fg=TEXT3).pack(pady=4)

    def _status_row(self, parent, label, initial):
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill="x", pady=2)
        dot = tk.Canvas(row, width=10, height=10, bg=BG2,
                        highlightthickness=0)
        dot.pack(side="left", padx=(0,8))
        dot.create_oval(1,1,9,9, fill=TEXT3, outline="", tags="dot")
        tk.Label(row, text=label, font=("Courier New", 9, "bold"),
                 bg=BG2, fg=TEXT, width=22, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=initial, font=("Courier New", 9),
                       bg=BG2, fg=TEXT3, anchor="w")
        lbl.pack(side="left")
        return dot, lbl

    def _set_status(self, dot_lbl, color, text):
        dot, lbl = dot_lbl
        dot.itemconfig("dot", fill=color)
        lbl.config(fg=color, text=text)

    # ── Logging
    def _log(self, msg, tag=""):
        ts = time.strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # ── Animation
    def _animate(self):
        self._angle  = (self._angle  + 1.8) % 360
        self._angle2 = (self._angle2 - 1.1) % 360
        self._angle3 = (self._angle3 + 3.5) % 360
        self._pulse  = (self._pulse  + 0.07) % (2 * math.pi)
        self._scan_y = (self._scan_y + 2.0) % 300

        self._draw_hud()
        self.root.after(33, self._animate)  # 30fps — plenty for smooth arcs

    def _arc(self, cx, cy, r, start, extent, color, width=1, dash=None):
        x0, y0 = cx-r, cy-r
        x1, y1 = cx+r, cy+r
        kw = dict(outline=color, fill="", width=width, style="arc",
                  start=start, extent=extent, tags="hud")
        if dash: kw["dash"] = dash
        self.canvas.create_arc(x0, y0, x1, y1, **kw)

    def _create_animated_items(self):
        """Pre-create all animated canvas items. _draw_hud just updates their coords."""
        c = self.canvas
        cx, cy = W//2, 165

        # Scanline
        self._id_scan = c.create_line(30, 0, W-30, 0, fill=CYAN, width=1,
                                      stipple="gray25")

        # Outer ring arcs (4 segments)
        self._id_outer = [
            c.create_arc(cx-128, cy-128, cx+128, cy+128,
                        outline=col, fill="", width=w, style="arc",
                        start=0, extent=ext)
            for col, w, ext in [(CYAN2,1,60),(CYAN2,1,50),(CYAN,2,80),(CYAN,2,40)]
        ]

        # Diamond markers (4)
        self._id_diamonds = []
        for _ in range(4):
            self._id_diamonds.append(
                c.create_polygon(0,0,0,0,0,0,0,0, fill=CYAN, outline=""))

        # Mid ring arcs (5 segments)
        self._id_mid = [
            c.create_arc(cx-106, cy-106, cx+106, cy+106,
                        outline=col, fill="", width=w, style="arc",
                        start=0, extent=ext)
            for col, w, ext in [(CYAN,2,45),(CYAN2,1,30),(CYAN,2,55),(DIM,1,25),(CYAN,2,50)]
        ]

        # Mid dots (3)
        self._id_mid_dots = [
            c.create_oval(0,0,6,6, fill=CYAN, outline="") for _ in range(3)
        ]

        # Inner ring arcs (5 segments)
        self._id_inner = [
            c.create_arc(cx-84, cy-84, cx+84, cy+84,
                        outline=col, fill="", width=w, style="arc",
                        start=0, extent=ext)
            for col, w, ext in [(CYAN,3,35),(CYAN2,2,20),(CYAN,3,40),(CYAN2,2,25),(CYAN,3,55)]
        ]

        # Core glow rings (3)
        self._id_glow = [
            c.create_oval(cx-40, cy-40, cx+40, cy+40,
                         fill="", outline=CYAN, width=max(1,3-i))
            for i in range(3)
        ]

        # Core fill
        self._id_core = c.create_oval(cx-28, cy-28, cx+28, cy+28,
                                      fill=BG3, outline=CYAN, width=2)

        # Status text
        self._id_status = c.create_text(cx, cy+9, text="STANDBY",
                                        fill=TEXT2, font=("Courier New", 7))

        # Raise static elements above animated ones
        c.tag_raise("static")

    def _draw_hud(self):
        c  = self.canvas
        cx, cy = W//2, 165
        pulse  = 0.85 + 0.15 * math.sin(self._pulse)
        glow_r = int(28 * pulse)

        # Scanline
        sy = int(self._scan_y)
        c.coords(self._id_scan, 30, sy, W-30, sy)

        # Outer arcs
        offsets = [0, 90, 190, 300]
        for arc_id, off in zip(self._id_outer, offsets):
            c.itemconfig(arc_id, start=self._angle2 + off)

        # Diamond markers
        for i, (dia_id, off) in enumerate(zip(self._id_diamonds, [0,90,180,270])):
            ang = math.radians(self._angle2 + off)
            mx = cx + 128*math.cos(ang)
            my = cy + 128*math.sin(ang)
            s = 4
            c.coords(dia_id, mx, my-s, mx+s, my, mx, my+s, mx-s, my)

        # Mid arcs
        mid_offsets = [0, 60, 130, 220, 280]
        for arc_id, off in zip(self._id_mid, mid_offsets):
            c.itemconfig(arc_id, start=self._angle + off)

        # Mid dots
        for dot_id, off in zip(self._id_mid_dots, [0, 120, 240]):
            ang = math.radians(self._angle + off)
            dx = cx + 106*math.cos(ang)
            dy = cy + 106*math.sin(ang)
            c.coords(dot_id, dx-3, dy-3, dx+3, dy+3)

        # Inner arcs
        inner_offsets = [0, 50, 110, 200, 270]
        for arc_id, off in zip(self._id_inner, inner_offsets):
            c.itemconfig(arc_id, start=self._angle3 + off)

        # Glow rings
        for i, (glow_id, extra) in enumerate(zip(self._id_glow, [16, 8, 0])):
            r = glow_r + extra
            c.coords(glow_id, cx-r, cy-r, cx+r, cy+r)

        # Core
        r_core = max(4, glow_r - 4)
        c.coords(self._id_core, cx-r_core, cy-r_core, cx+r_core, cy+r_core)

        # Status text
        status_txt = "ONLINE" if self._running else "STANDBY"
        c.itemconfig(self._id_status, text=status_txt)

    # ── Ollama check
    def _check_ollama(self):
        try:
            import urllib.request
            urllib.request.urlopen(OLLAMA_URL, timeout=2)
            return True
        except: return False

    def _check_ollama_loop(self):
        ok = self._check_ollama()
        if ok:
            self._set_status(self._dot_ollama, CYAN, "Running")
            self.ollama_btn.config(state="disabled")
        else:
            self._set_status(self._dot_ollama, RED, "Not running")
            self.ollama_btn.config(state="normal")
        self.root.after(5000, self._check_ollama_loop)

    def _start_ollama(self):
        self._log("Starting Ollama...", "")
        try:
            subprocess.Popen(["ollama", "serve"],
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
            self._log("Ollama started.", "ok")
        except Exception as e:
            self._log(f"Ollama failed: {e}", "err")

    # ── Launch / Stop
    def _toggle(self):
        if self._running: self._stop()
        else:             self._start()

    def _start(self):
        if not self._check_ollama():
            self._log("Ollama not running — click Start Ollama first.", "warn")
            return
        self._log("Launching Core Nexus...", "nexus")
        self._running = True
        self.launch_btn.config(text="■   STOP NEXUS", bg=RED, fg="white",
                                activebackground="#cc0033", activeforeground="white")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            self.server_proc = subprocess.Popen(
                [PYTHON, SERVER_SCRIPT], cwd=BASE_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            self._set_status(self._dot_server, YELLOW, "Starting...")
            threading.Thread(target=self._watch, args=(self.server_proc,"S",
                self._dot_server, "8080"), daemon=True).start()
        except Exception as e:
            self._log(f"Server error: {e}", "err")
        try:
            self.voice_proc = subprocess.Popen(
                [PYTHON, VOICE_SCRIPT], cwd=BASE_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            self._set_status(self._dot_voice, YELLOW, "Starting...")
            threading.Thread(target=self._watch, args=(self.voice_proc,"V",
                self._dot_voice, "Microphone ready"), daemon=True).start()
        except Exception as e:
            self._log(f"Voice error: {e}", "err")
        self.root.after(3000, lambda: self.web_btn.config(state="normal"))

    def _stop(self):
        self._log("Stopping Core Nexus...", "warn")
        self._running = False
        self.launch_btn.config(text="▶   LAUNCH NEXUS", bg=CYAN, fg=BG,
                                activebackground=CYAN2, activeforeground=BG)
        self.web_btn.config(state="disabled")
        for proc in [self.server_proc, self.voice_proc]:
            if proc:
                try: proc.terminate(); proc.wait(timeout=3)
                except:
                    try: proc.kill()
                    except: pass
        self.server_proc = self.voice_proc = None
        self._set_status(self._dot_voice,  TEXT3, "Stopped")
        self._set_status(self._dot_server, TEXT3, "Stopped")
        self._log("Core Nexus stopped.", "")

    def _watch(self, proc, prefix, dot_lbl, ready_keyword):
        for line in iter(proc.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").strip()
            if not text: continue
            tag = "err" if any(w in text.lower() for w in ["error","traceback","exception"]) else ""
            if "NEXUS >" in text:
                tag = "nexus"
                text = "Nexus: " + text.replace("NEXUS >","").strip()
            self.root.after(0, lambda t=text, tg=tag: self._log(f"{prefix}: {t}", tg))
            if ready_keyword in text:
                self.root.after(0, lambda: self._set_status(dot_lbl, CYAN, "Running"))
        if self._running:
            self.root.after(0, lambda: self._set_status(dot_lbl, RED, "Crashed"))
            self.root.after(0, lambda: self._log(f"{prefix}: Process stopped unexpectedly.", "err"))

    def _on_close(self):
        if self._running: self._stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app  = HUDLauncher(root)
    root.mainloop()
