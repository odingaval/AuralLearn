import os
import streamlit as st

from modules.stt import render_browser_stt
from modules.intent import detect_intent
from modules.llm import explain_concept, generate_quiz
from modules.tts import synthesize, cleanup


st.set_page_config(page_title="AuralLearn", layout="centered")

st.title("AuralLearn")
st.caption("Audio-first classroom assistant (STT → Intent → LLM → TTS)")

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None


def _get_transcript_from_ui():
    transcript = render_browser_stt()
    return transcript


def _ensure_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY is not set. Add it to environment variables or a .env file."
        )
        st.stop()


def _play_mp3(mp3_path: str):
    if not mp3_path:
        return
    st.audio(mp3_path, format="audio/mp3")


transcript = _get_transcript_from_ui()

if transcript:
    st.session_state.last_transcript = transcript.strip()

if st.session_state.last_transcript:
    st.subheader("Recognized text")
    st.write(st.session_state.last_transcript)

    if st.button("Generate (Explain/Quiz)" , type="primary"):
        _ensure_api_key()
        with st.spinner("Detecting intent & generating content..."):
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
                        st.markdown(f"### {visual.get('title','')}")
                        points = visual.get("points", [])
                        if points:
                            for p in points:
                                st.write(f"- {p}")
                        analogy = visual.get("analogy")
                        if analogy:
                            st.info(f"Analogy: {analogy}")

                    speech = result.get("speech", "")
                    if speech:
                        st.write(speech)
                        mp3 = synthesize(speech)
                        _play_mp3(mp3)
                        cleanup(mp3)

                elif parsed.intent == "quiz":
                    n = parsed.n_questions
                    result = generate_quiz(parsed.topic, n=n)

                    st.subheader(f"Quiz ({n} MCQs)")
                    questions = result.get("questions", [])

                    for i, q in enumerate(questions, start=1):
                        st.markdown(f"### Q{i}. {q.get('q','')}")
                        options = q.get("options", [])
                        for opt in options:
                            st.write(f"- {opt}")
                        st.success(f"Answer: {q.get('answer','')}")
                        expl = q.get("explanation")
                        if expl:
                            with st.expander("Explanation"):
                                st.write(expl)

                        speech = q.get("speech")
                        if speech:
                            mp3 = synthesize(speech)
                            st.audio(mp3, format="audio/mp3")
                            cleanup(mp3)

