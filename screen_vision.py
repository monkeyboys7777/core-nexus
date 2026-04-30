"""
screen_vision.py — Core Nexus Screen Vision
Captures a screenshot and asks the AI to describe / analyse it.
Uses gemma3:4b's built-in vision capability via Ollama.
Requires: pip install mss pillow
"""

import os
import base64
import json
import urllib.request
from io import BytesIO

OLLAMA_URL   = "http://localhost:11434/api/chat"
VISION_MODEL = "gemma3:4b"   # gemma3 supports vision natively

try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def capture_screenshot(monitor_index: int = 0, max_width: int = 1280) -> bytes | None:
    """
    Capture a screenshot of the selected monitor.
    monitor_index 0 = all monitors combined, 1+ = individual monitors.
    Downsizes to max_width to keep payload small for the model.
    Returns PNG bytes, or None on failure.
    """
    if not MSS_AVAILABLE:
        print("  [VISION] mss not installed. Run: pip install mss")
        return None
    if not PIL_AVAILABLE:
        print("  [VISION] Pillow not installed. Run: pip install pillow")
        return None

    try:
        with mss.mss() as sct:
            monitors = sct.monitors   # [0]=all, [1]=first, [2]=second...
            idx      = min(monitor_index + 1, len(monitors) - 1)
            monitor  = monitors[idx]
            sct_img  = sct.grab(monitor)

        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # Downsize to keep token count reasonable
        if img.width > max_width:
            ratio  = max_width / img.width
            new_h  = int(img.height * ratio)
            img    = img.resize((max_width, new_h), Image.LANCZOS)

        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    except Exception as e:
        print(f"  [VISION] Screenshot failed: {e}")
        return None


def ask_vision(question: str, screenshot_bytes: bytes) -> str:
    """
    Send screenshot + question to Ollama vision model.
    Returns the model's text description.
    """
    img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

    payload = {
        "model":  VISION_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": question,
                "images": [img_b64]
            }
        ],
        "options": {
            "temperature": 0.3,
            "num_predict": 300,
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            OLLAMA_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return result["message"]["content"].strip()
    except Exception as e:
        return f"Vision query failed: {e}"


def describe_screen(monitor_index: int = 0) -> str:
    """
    Capture and describe what is currently on screen.
    Returns a plain-English description.
    """
    screenshot = capture_screenshot(monitor_index)
    if not screenshot:
        return "Could not capture screenshot."

    return ask_vision(
        "Describe what is currently visible on screen. "
        "Be concise — mention the main application, any visible content, "
        "and any notable UI elements. One short paragraph.",
        screenshot
    )


def analyse_screen(question: str, monitor_index: int = 0) -> str:
    """
    Capture screen and answer a specific question about it.
    """
    screenshot = capture_screenshot(monitor_index)
    if not screenshot:
        return "Could not capture screenshot."

    return ask_vision(question, screenshot)


def list_monitors() -> list[dict]:
    """Return available monitors."""
    if not MSS_AVAILABLE:
        return []
    with mss.mss() as sct:
        return [
            {"index": i, "width": m["width"], "height": m["height"]}
            for i, m in enumerate(sct.monitors[1:], start=1)
        ]
