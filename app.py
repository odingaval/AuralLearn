import os
import streamlit as st
from dotenv import load_dotenv

from modules.stt import render_browser_stt, transcribe_with_whisper
from modules.intent import detect_intent
from modules.llm import explain_concept, generate_quiz
from modules.tts import synthesize, cleanup

load_dotenv()  # load ANTHROPIC_API_KEY and OPENAI_API_KEY from .env if present

st.set_page_config(page_title="AuralLearn", layout="centered")

st.title("AuralLearn")
st.caption("Audio-first classroom assistant (STT \u2192 Intent \u2192 LLM \u2192 TTS)")

# \u2500\u2500 Session state init \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None


# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _ensure_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY is not set. Add it to a .env file or your environment."
        )
        st.stop()


def _play_audio(mp3_path: str):
    """
    Read the MP3 into memory first, then delete the temp file, then render.
    This avoids the race condition where st.audio() (non-blocking) renders
    a widget while the file is already deleted by cleanup().
    """
    if not mp3_path:
        return
    try:
        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()
        cleanup(mp3_path)  # safe to delete now — bytes are in memory
        st.audio(audio_bytes, format="audio/mp3")
    except OSError:
        pass


# \u2500\u2500 STT input (two tabs) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

tab_mic, tab_upload = st.tabs(["Microphone (Browser)", "Upload Audio (Whisper)"])

with tab_mic:
    transcript = render_browser_stt()
    # Only update session state when a new, different transcript arrives
    if transcript and transcript.strip() != st.session_state.last_transcript:
        st.session_state.last_transcript = transcript.strip()

with tab_upload:
    uploaded = st.file_uploader(
        "Upload a WAV, MP3, or M4A file",
        type=["wav", "mp3", "m4a"],
        help="Uses OpenAI Whisper. Requires OPENAI_API_KEY in your environment or .env.",
    )
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if uploaded:
        if st.button("Transcribe with Whisper", id="btn-whisper"):
            if not openai_key:
                st.error("OPENAI_API_KEY not set. Add it to your .env file.")
            else:
                with st.spinner("Transcribing audio..."):
                    try:
                        result = transcribe_with_whisper(
                            uploaded.read(), api_key=openai_key
                        )
                        st.session_state.last_transcript = result.strip()
                        st.success(f"Transcribed: {result}")
                    except Exception as e:
                        st.error(f"Whisper transcription failed: {e}")


# \u2500\u2500 Transcript display + Clear \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

if st.session_state.last_transcript:
    col_text, col_clear = st.columns([5, 1])

    with col_text:
        st.subheader("Recognized text")
        st.write(st.session_state.last_transcript)

    with col_clear:
        st.write("")  # vertical alignment spacer
        if st.button("Clear", use_container_width=True, id="btn-clear"):
            st.session_state.last_transcript = None
            st.session_state.last_payload = None
            st.rerun()

    # \u2500\u2500 Generate \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    if st.button("Generate (Explain / Quiz)", type="primary", id="btn-generate"):
        _ensure_api_key()
        with st.spinner("Detecting intent & generating content..."):
            try:
                parsed = detect_intent(st.session_state.last_transcript)

                if parsed.intent == "unknown":
                    st.warning(
                        "Could not detect intent. Try phrasing like:\n"
                        "- 'samjhao photosynthesis' (explain)\n"
                        "- 'quiz lo photosynthesis 5 questions' (quiz)"
                    )
                else:
                    st.session_state.last_payload = parsed

                    if parsed.intent == "explain":
                        result = explain_concept(parsed.topic)

                        st.subheader("Explanation")
                        visual = result.get("visual", {})
                        if visual:
                            st.markdown(f"### {visual.get('title', '')}")
                            points = visual.get("points", [])
                            for p in points:
                                st.write(f"- {p}")
                            analogy = visual.get("analogy")
                            if analogy:
                                st.info(f"Analogy: {analogy}")

                        speech = result.get("speech", "")
                        if speech:
                            st.write(speech)
                            mp3 = synthesize(speech)
                            _play_audio(mp3)

                    elif parsed.intent == "quiz":
                        n = parsed.n_questions
                        result = generate_quiz(parsed.topic, n=n)

                        st.subheader(f"Quiz ({n} MCQs)")
                        questions = result.get("questions", [])

                        for i, q in enumerate(questions, start=1):
                            st.markdown(f"### Q{i}. {q.get('q', '')}")
                            options = q.get("options", [])
                            for opt in options:
                                st.write(f"- {opt}")
                            st.success(f"Answer: {q.get('answer', '')}")
                            expl = q.get("explanation")
                            if expl:
                                with st.expander("Explanation"):
                                    st.write(expl)
                            speech = q.get("speech")
                            if speech:
                                mp3 = synthesize(speech)
                                _play_audio(mp3)

            except Exception as e:
                st.error(f"Something went wrong: {e}")
