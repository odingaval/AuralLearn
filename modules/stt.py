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
<script>
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    document.getElementById('stt-status').innerText = 'Your browser does not support Speech Recognition. Please use Chrome or Edge.';
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'hi-IN';          // Hindi — also picks up Hinglish well
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    const statusEl  = document.getElementById('stt-status');
    const resultEl  = document.getElementById('stt-result');
    const btn       = document.getElementById('stt-btn');

    let isListening = false;

    btn.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
            return;
        }
        recognition.start();
        isListening = true;
        btn.innerText = 'Stop Listening';
        statusEl.innerText = 'Listening...';
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        resultEl.value = transcript;
        statusEl.innerText = 'Processing...';

        // Navigate the parent Streamlit page so query params include the transcript.
        // Using window.parent ensures we update the top-level page, not just the iframe.
        const url = new URL(window.parent.location.href);
        url.searchParams.set('transcript', transcript);
        window.parent.location.href = url.toString();
    };

    recognition.onerror = (event) => {
        statusEl.innerText = 'Error: ' + event.error;
        isListening = false;
        btn.innerText = 'Start Listening';
    };

    recognition.onend = () => {
        isListening = false;
        btn.innerText = 'Start Listening';
        statusEl.innerText = 'Click to speak again.';
    };
}
</script>

<div style="text-align:center; font-family:sans-serif;">
  <button id="stt-btn"
    style="font-size:1.4rem; padding:14px 28px; border-radius:12px;
           background:#FF4B4B; color:white; border:none; cursor:pointer;
           box-shadow:0 4px 15px rgba(255,75,75,0.4);">
    Start Listening
  </button>
  <p id="stt-status" style="margin-top:10px; color:#aaa; font-size:0.9rem;">
    Click the button and speak in Hindi or Hinglish.
  </p>
  <textarea id="stt-result" rows="2"
    style="width:90%; margin-top:8px; font-size:1rem; border-radius:8px;
           padding:8px; border:1px solid #444; background:#111; color:#eee;"
    placeholder="Your speech will appear here..." readonly></textarea>
</div>
"""


def render_browser_stt() -> str | None:
    """
    Renders the Web Speech API component in Streamlit.
    Returns the transcript string if captured via query params, else None.
    """
    # Check if a transcript was submitted via query params
    params = st.query_params
    transcript = params.get("transcript", None)

    components.html(SPEECH_RECOGNITION_JS, height=180)

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
