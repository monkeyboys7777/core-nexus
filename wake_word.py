"""
wake_word.py — Core Nexus Wake Word Detection
Uses openwakeword for fully offline, no-account wake word detection.

Setup:
  pip install openwakeword

No API key, no account, no internet required after install.

Built-in wake words (set "wake_keyword" in config.json):
  hey_jarvis     — "Hey Jarvis"  (default — fits the Iron Man theme)
  alexa          — "Alexa"
  hey_mycroft    — "Hey Mycroft"
  hey_rhasspy    — "Hey Rhasspy"

Custom "Nexus" wake word:
  Train one free at https://openWakeWord.com or use the
  openwakeword training tools to generate a custom .tflite model.
  Place it in F:\\Projects\\ai\\nexus_wakeword.tflite
  Set "wake_keyword": "nexus_wakeword" in config.json
"""

import os
import threading
import numpy as np

CUSTOM_MODEL_PATH = os.path.join(os.path.dirname(__file__), "nexus_wakeword.tflite")
DEFAULT_KEYWORD   = "hey_jarvis"

try:
    from openwakeword.model import Model as WakeModel
    OWW_AVAILABLE = True
except ImportError:
    OWW_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

SAMPLE_RATE  = 16000
CHUNK_FRAMES = 1280
CHANNELS     = 1


class WakeWordDetector:
    """
    Always-on offline wake word listener using openwakeword.
    Fires on_wake() callback when the wake word is detected.
    Falls back gracefully if unavailable.
    """

    def __init__(self, access_key: str, on_wake, keyword: str = DEFAULT_KEYWORD):
        """
        access_key : ignored (kept for API compatibility)
        on_wake    : callback fired when wake word detected
        keyword    : wake word model name
        """
        self.on_wake  = on_wake
        self._running = False
        self._thread  = None
        self._model   = None
        self._audio   = None
        self._stream  = None
        self._ready   = False
        self._keyword = keyword

        if not OWW_AVAILABLE:
            print("  [WAKE] openwakeword not installed. Run: pip install openwakeword")
            print("  [WAKE] Falling back to phrase-in-speech detection.")
            return

        if not PYAUDIO_AVAILABLE:
            print("  [WAKE] pyaudio not available.")
            print("  [WAKE] Falling back to phrase-in-speech detection.")
            return

        try:
            if os.path.exists(CUSTOM_MODEL_PATH):
                self._model   = WakeModel(wakeword_models=[CUSTOM_MODEL_PATH])
                self._keyword = os.path.splitext(os.path.basename(CUSTOM_MODEL_PATH))[0]
                print(f"  [WAKE] Custom wake word loaded: {self._keyword}")
            else:
                self._model   = WakeModel(wakeword_models=[keyword])
                self._keyword = keyword
                if keyword == DEFAULT_KEYWORD:
                    print(f"  [WAKE] Wake word: 'Hey Jarvis' (say this to activate)")
                else:
                    print(f"  [WAKE] Wake word: '{keyword}'")
                print(f"  [WAKE] Tip: change wake_keyword in config.json for other words.")

            self._ready = True
            print("  [WAKE] openwakeword ready — fully offline, no account needed.")

        except Exception as e:
            print(f"  [WAKE] openwakeword init failed: {e}")
            print("  [WAKE] Falling back to phrase-in-speech detection.")

    def start(self):
        if not self._ready:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("  [WAKE] Listening for wake word...")

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass

    def _listen_loop(self):
        try:
            import pyaudio as pa
            self._audio  = pa.PyAudio()
            self._stream = self._audio.open(
                rate=SAMPLE_RATE,
                channels=CHANNELS,
                format=pa.paInt16,
                input=True,
                frames_per_buffer=CHUNK_FRAMES
            )

            threshold = 0.5

            while self._running:
                raw   = self._stream.read(CHUNK_FRAMES, exception_on_overflow=False)
                audio = np.frombuffer(raw, dtype=np.int16)
                preds = self._model.predict(audio)

                for model_name, score in preds.items():
                    if score >= threshold:
                        print(f"  [WAKE] '{model_name}' detected (score: {score:.2f})")
                        self._model.reset()
                        self.on_wake()
                        break

        except Exception as e:
            if self._running:
                print(f"  [WAKE] Listener error: {e}")
        finally:
            self.stop()

    def cleanup(self):
        self.stop()

    @property
    def is_active(self) -> bool:
        return self._ready and self._running
