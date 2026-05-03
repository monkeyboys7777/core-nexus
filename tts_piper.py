"""
tts_piper.py — Core Nexus Neural TTS
Uses Piper for high-quality local neural speech synthesis.
Falls back to pyttsx3 if Piper is unavailable.

Setup:
  pip install piper-tts sounddevice numpy

Voice model downloads automatically on first use.
Default: en_GB-alan-medium (British male butler voice)
"""

import os
import sys
import wave
import tempfile
import urllib.request
import threading

MODELS_DIR   = os.path.join(os.path.dirname(__file__), "piper_models")
VOICE_NAME   = "en_GB-alan-medium"
MODEL_URL    = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx"
CONFIG_URL   = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json"
MODEL_PATH   = os.path.join(MODELS_DIR, f"{VOICE_NAME}.onnx")
CONFIG_PATH  = os.path.join(MODELS_DIR, f"{VOICE_NAME}.onnx.json")

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

try:
    import sounddevice as sd
    import numpy as np
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


def _download_model():
    """Download Piper voice model if not already present."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print(f"  [TTS] Downloading voice model: {VOICE_NAME}")
        print(f"  [TTS] This is a one-time download (~60MB)...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            urllib.request.urlretrieve(CONFIG_URL, CONFIG_PATH)
            print(f"  [TTS] Voice model ready.")
        except Exception as e:
            print(f"  [TTS] Download failed: {e}")
            if os.path.exists(MODEL_PATH):
                os.remove(MODEL_PATH)
            return False
    return True


class PiperSpeaker:
    """
    Neural TTS speaker using Piper.
    Sounds significantly more natural than pyttsx3.
    """
    def __init__(self):
        self.voice   = None
        self._lock   = threading.Lock()
        self._ready  = False
        self._fallback = None

        if not PIPER_AVAILABLE:
            print("  [TTS] piper-tts not installed. Run: pip install piper-tts sounddevice")
            self._init_fallback()
            return

        if not SD_AVAILABLE:
            print("  [TTS] sounddevice not installed. Run: pip install sounddevice")
            self._init_fallback()
            return

        if _download_model():
            try:
                self.voice  = PiperVoice.load(MODEL_PATH)
                self._ready = True
                print(f"  [TTS] Piper voice loaded: {VOICE_NAME}")
            except Exception as e:
                print(f"  [TTS] Piper load failed: {e}")
                self._init_fallback()
        else:
            self._init_fallback()

    def _init_fallback(self):
        """Set up pyttsx3 as fallback."""
        if PYTTSX3_AVAILABLE:
            try:
                self._fallback = pyttsx3.init()
                self._fallback.setProperty("rate", 185)
                voices = self._fallback.getProperty("voices")
                for v in voices:
                    if "david" in v.name.lower() or "zira" in v.name.lower():
                        self._fallback.setProperty("voice", v.id)
                        break
                print("  [TTS] Falling back to pyttsx3.")
            except Exception as e:
                print(f"  [TTS] pyttsx3 fallback also failed: {e}")
                self._fallback = None

    def say(self, text: str):
        """Speak text. Thread-safe."""
        with self._lock:
            if self._ready and self.voice:
                self._say_piper(text)
            elif self._fallback:
                self._say_pyttsx3(text)

    def _say_piper(self, text: str):
        try:
            import wave, tempfile, os
            sample_rate = self.voice.config.sample_rate
            num_channels = 1
            sample_width = 2  # 16-bit = 2 bytes

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            # Pre-configure wav file so Piper can write to it
            with wave.open(tmp_path, "wb") as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                self.voice.synthesize(text, wav_file)

            # Play back
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(tmp_path, dtype="float32")
            sd.play(data, samplerate=sr)
            sd.wait()
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception as e:
            print(f"  [TTS] Piper speak error: {e}")
            if self._fallback:
                self._say_pyttsx3(text)

    def _say_pyttsx3(self, text: str):
        try:
            self._fallback.say(text)
            self._fallback.runAndWait()
        except Exception as e:
            print(f"  [TTS] pyttsx3 speak error: {e}")

    @property
    def is_neural(self) -> bool:
        return self._ready
