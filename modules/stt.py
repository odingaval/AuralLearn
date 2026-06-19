"""
stt.py — Speech-to-Text handling.

Strategy:
1. Browser Web Speech API (JavaScript injection via Streamlit components) — free, no API key, supports Hindi.
2. Whisper API fallback for uploaded audio.

The browser STT is the primary path because:
- Works offline (uses device microphone directly)
- Supports Hindi (hi-IN) natively in Chrome/Edge
- Zero latency to transcription (streaming)
"""

import streamlit as st
import streamlit.components.v1 as components


# ── Browser-based STT (Web Speech API) ─────────────────────────────────────────

SPEECH_RECOGNITION_JS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

  #stt-btn {
    font-size: 1rem;
    font-weight: 600;
    padding: 12px 36px;
    border-radius: 14px;
    background: linear-gradient(135deg, #0d9488, #059669);
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(13,148,136,0.5);
    letter-spacing: 0.3px;
    transition: transform 0.2s, box-shadow 0.2s;
    font-family: 'Inter', sans-serif;
  }
  #stt-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(13,148,136,0.65);
  }
  #stt-btn.listening {
    background: linear-gradient(135deg, #ea580c, #dc2626);
    box-shadow: 0 4px 20px rgba(234,88,12,0.55);
    animation: pulse-ring 1.5s ease-out infinite;
  }
  @keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0px rgba(234,88,12,0.55); }
    70%  { box-shadow: 0 0 0 14px rgba(234,88,12,0); }
    100% { box-shadow: 0 0 0 0px rgba(234,88,12,0); }
  }
  #stt-status {
    margin-top: 10px;
    font-size: 0.82rem;
    letter-spacing: 0.2px;
    color: #475569;
    font-family: 'Inter', sans-serif;
    transition: color 0.3s;
  }
  #stt-result {
    width: 88%;
    margin-top: 8px;
    font-size: 0.95rem;
    border-radius: 10px;
    padding: 10px 14px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    color: #e2e8f0;
    resize: none;
    outline: none;
    font-family: 'Inter', sans-serif;
    box-sizing: border-box;
  }
</style>

<script>
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    document.getElementById('stt-status').innerText = 'Browser not supported. Use Chrome or Edge.';
    document.getElementById('stt-status').style.color = '#f87171';
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'hi-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    const statusEl = document.getElementById('stt-status');
    const resultEl = document.getElementById('stt-result');
    const btn      = document.getElementById('stt-btn');

    let isListening = false;

    btn.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
            return;
        }
        recognition.start();
        isListening = true;
        btn.innerHTML = '&#9209; Stop Listening';
        btn.classList.add('listening');
        statusEl.innerText = 'Listening\u2026';
        statusEl.style.color = '#f87171';
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        resultEl.value = transcript;
        statusEl.innerText = '\u2705 Got it! Sending\u2026';
        statusEl.style.color = '#6ee7b7';

        const url = new URL(window.parent.location.href);
        url.searchParams.set('transcript', transcript);
        window.parent.location.href = url.toString();
    };

    recognition.onerror = (event) => {
        statusEl.innerText = '\u26a0 Error: ' + event.error;
        statusEl.style.color = '#fbbf24';
        isListening = false;
        btn.innerHTML = '\ud83c\udfa4 Start Listening';
        btn.classList.remove('listening');
    };

    recognition.onend = () => {
        isListening = false;
        btn.innerHTML = '\ud83c\udfa4 Start Listening';
        btn.classList.remove('listening');
        if (!resultEl.value) {
            statusEl.innerText = 'Click to speak again.';
            statusEl.style.color = '#475569';
        }
    };
}
</script>

<div style="text-align:center; padding: 0.5rem 0;">
  <button id="stt-btn">&#127908; Start Listening</button>
  <p id="stt-status">Click and speak in Hindi or Hinglish</p>
  <textarea id="stt-result" rows="2"
    placeholder="Your speech will appear here\u2026" readonly></textarea>
</div>
"""


def render_browser_stt() -> str | None:
    """
    Renders the Web Speech API component in Streamlit.
    Returns the transcript string if captured via query params, else None.
    """
    params = st.query_params
    transcript = params.get("transcript", None)

    components.html(SPEECH_RECOGNITION_JS, height=190)

    return transcript


# ── Whisper fallback (uploaded audio) ──────────────────────────────────────────

def transcribe_with_whisper(audio_bytes: bytes, api_key: str) -> str:
    """
    Use OpenAI Whisper API to transcribe uploaded audio.
    Only needed when browser STT isn't available.
    """
    import openai
    import tempfile, os

    client = openai.OpenAI(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="hi",  # Hindi — handles Hinglish well
        )
    os.unlink(tmp_path)
    return response.text
