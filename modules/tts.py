"""
tts.py — Text-to-speech using edge-tts (free, low latency, Hindi/English voices).
Falls back to gTTS if edge-tts is unavailable.
"""

import asyncio
import concurrent.futures
import os
import tempfile
from pathlib import Path

# ── Voice settings ─────────────────────────────────────────────────────────────
# Hindi female voice — sounds natural for Hinglish content
EDGE_VOICE_HINDI   = "hi-IN-SwaraNeural"   # Hindi (India) — Female
EDGE_VOICE_ENGLISH = "en-IN-NeerjaNeural"  # English (India) — Female accent

DEFAULT_VOICE = EDGE_VOICE_HINDI
SPEECH_RATE   = "+0%"   # normal speed; try "+10%" if you want faster


# ── edge-tts (primary) ─────────────────────────────────────────────────────────

async def _edge_tts_to_file(text: str, voice: str, output_path: str) -> None:
    """Async helper — calls edge-tts and saves MP3."""
    import edge_tts  # lazy import so ImportError is caught below
    communicate = edge_tts.Communicate(text, voice, rate=SPEECH_RATE)
    await communicate.save(output_path)


def speak_edge(text: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Convert text → MP3 using edge-tts.
    Runs in a thread pool so asyncio.run() gets a fresh event loop,
    avoiding conflicts with Streamlit's own running event loop.
    Returns the path to the saved MP3 file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, _edge_tts_to_file(text, voice, tmp.name)).result()
    return tmp.name


# ── gTTS fallback ──────────────────────────────────────────────────────────────

def speak_gtts(text: str, lang: str = "hi") -> str:
    """
    Fallback TTS using gTTS.
    lang='hi' for Hindi, 'en' for English.
    Returns path to saved MP3 file.
    """
    from gtts import gTTS  # lazy import
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(tmp.name)
    return tmp.name


# ── Public API ─────────────────────────────────────────────────────────────────

def synthesize(text: str) -> str:
    """
    Main entry point. Tries edge-tts first; falls back to gTTS.
    Returns path to the generated audio file.
    """
    try:
        return speak_edge(text)
    except ImportError:
        print("[TTS] edge-tts not found, falling back to gTTS.")
        return speak_gtts(text, lang="hi")
    except Exception as e:
        print(f"[TTS] edge-tts error ({e}), falling back to gTTS.")
        return speak_gtts(text, lang="hi")


def cleanup(path: str) -> None:
    """Delete a temporary audio file after playback."""
    try:
        os.unlink(path)
    except OSError:
        pass
