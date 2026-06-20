import os
import streamlit as st
from dotenv import load_dotenv

from modules.stt import render_browser_stt, transcribe_with_whisper
from modules.intent import detect_intent
from modules.llm import explain_concept, generate_quiz
from modules.tts import synthesize, cleanup

load_dotenv()  # load OPENAI_API_KEY (for Whisper) and OLLAMA_MODEL from .env if present

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AuralLearn — Classroom AI Assistant",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Base reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 40%, #0a0f1a 100%);
    min-height: 100vh;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 780px;
}

/* ── Hero header ── */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    margin-bottom: 0.5rem;
}
.hero-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    margin: 0;
}
.hero-tagline {
    color: #64748b;
    font-size: 0.95rem;
    margin-top: 0.4rem;
    font-weight: 400;
    letter-spacing: 0.3px;
}
.hero-badge {
    display: inline-block;
    background: rgba(167, 139, 250, 0.12);
    border: 1px solid rgba(167, 139, 250, 0.25);
    color: #a78bfa;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    margin-top: 0.8rem;
    letter-spacing: 0.5px;
}

/* ── Glass card ── */
.glass-card {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.8rem;
    backdrop-filter: blur(12px);
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

/* ── Section label ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 1rem;
}

/* ── Transcript box ── */
.transcript-box {
    background: rgba(96, 165, 250, 0.06);
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    color: #e2e8f0;
    font-size: 1.05rem;
    line-height: 1.6;
    font-style: italic;
    margin-bottom: 1rem;
    position: relative;
}
.transcript-box::before {
    content: '"';
    position: absolute;
    top: -10px;
    left: 16px;
    font-size: 3rem;
    color: rgba(96, 165, 250, 0.3);
    font-family: Georgia, serif;
    line-height: 1;
}

/* ── Result cards ── */
.result-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 0.8rem;
}
.result-point {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #cbd5e1;
    font-size: 0.95rem;
    line-height: 1.5;
}
.result-point:last-child { border-bottom: none; }
.point-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    margin-top: 7px;
    flex-shrink: 0;
}
.analogy-box {
    background: rgba(52, 211, 153, 0.08);
    border: 1px solid rgba(52, 211, 153, 0.2);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    color: #6ee7b7;
    font-size: 0.9rem;
    margin-top: 1rem;
    display: flex;
    gap: 10px;
    align-items: flex-start;
}

/* ── Quiz cards ── */
.quiz-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.quiz-card:hover { border-color: rgba(167,139,250,0.3); }
.quiz-q {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 1rem;
    margin-bottom: 0.8rem;
    line-height: 1.5;
}
.quiz-option {
    padding: 0.4rem 0;
    color: #94a3b8;
    font-size: 0.9rem;
}
.quiz-answer {
    margin-top: 0.8rem;
    background: rgba(52, 211, 153, 0.1);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    color: #6ee7b7;
    font-size: 0.88rem;
    font-weight: 500;
}
.quiz-num {
    display: inline-block;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    color: white;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}

/* ── Streamlit tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.07);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 8px 20px;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(167,139,250,0.25), rgba(96,165,250,0.25)) !important;
    color: #c4b5fd !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.2rem;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.65rem 2rem;
    transition: all 0.25s;
    box-shadow: 0 4px 20px rgba(124,58,237,0.35);
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(124,58,237,0.5);
    filter: brightness(1.1);
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.06);
    box-shadow: none;
    border: 1px solid rgba(255,255,255,0.1);
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.1);
    box-shadow: none;
    transform: none;
}

/* ── File uploader ── */
.stFileUploader {
    border: 2px dashed rgba(167,139,250,0.25) !important;
    border-radius: 14px !important;
    background: rgba(167,139,250,0.04) !important;
    padding: 1rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #a78bfa !important; }

/* ── Alert/info boxes ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* ── Divider ── */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(167,139,250,0.3), rgba(96,165,250,0.3), transparent);
    margin: 1.5rem 0;
    border: none;
}

/* ── Step indicators ── */
.steps-row {
    display: flex;
    justify-content: center;
    gap: 0;
    margin: 1rem 0 2rem;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.step-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    font-weight: 700;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #475569;
}
.step-circle.active {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    border-color: transparent;
    color: white;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4);
}
.step-label {
    font-size: 0.68rem;
    color: #475569;
    font-weight: 500;
    text-align: center;
    max-width: 60px;
}
.step-connector {
    width: 40px;
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin-top: 18px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────────────────────────

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ensure_api_key():
    pass  # No API key needed — using local Ollama


def _play_audio(mp3_path: str):
    if not mp3_path:
        return
    try:
        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()
        cleanup(mp3_path)
        st.audio(audio_bytes, format="audio/mp3")
    except OSError:
        pass


# ── Hero Header ────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <h1 class="hero-logo">🎧 AuralLearn</h1>
    <p class="hero-tagline">Audio-first classroom assistant for Hinglish learners</p>
    <span class="hero-badge">Haryana Government Schools · Grades 6–10</span>
</div>

<div class="steps-row">
    <div class="step-item">
        <div class="step-circle active">1</div>
        <div class="step-label">Speak</div>
    </div>
    <div class="step-connector"></div>
    <div class="step-item">
        <div class="step-circle active">2</div>
        <div class="step-label">Detect</div>
    </div>
    <div class="step-connector"></div>
    <div class="step-item">
        <div class="step-circle active">3</div>
        <div class="step-label">Generate</div>
    </div>
    <div class="step-connector"></div>
    <div class="step-item">
        <div class="step-circle active">4</div>
        <div class="step-label">Listen</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── STT Input ──────────────────────────────────────────────────────────────────

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">Voice Input</div>', unsafe_allow_html=True)

tab_mic, tab_upload, tab_demo = st.tabs([
    "Microphone (Browser)", "Upload Audio (Whisper)", "Type it (Demo Mode)"
])

with tab_mic:
    transcript = render_browser_stt()
    if transcript and transcript.strip() != st.session_state.last_transcript:
        st.session_state.last_transcript = transcript.strip()

with tab_upload:
    uploaded = st.file_uploader(
        "Upload a WAV, MP3, or M4A file",
        type=["wav", "mp3", "m4a"],
        help="Uses OpenAI Whisper API. Requires OPENAI_API_KEY in your .env file.",
        label_visibility="collapsed",
    )
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if uploaded:
        st.markdown(f"**File:** `{uploaded.name}`")
        if st.button("Transcribe with Whisper", key="btn-whisper"):
            if not openai_key:
                st.error("OPENAI_API_KEY not set. Add it to your .env file.")
            else:
                with st.spinner("Transcribing audio…"):
                    try:
                        result = transcribe_with_whisper(uploaded.read(), api_key=openai_key)
                        st.session_state.last_transcript = result.strip()
                        st.success(f"Transcribed: {result}")
                    except Exception as e:
                        st.error(f"Whisper transcription failed: {e}")

with tab_demo:
    st.markdown(
        '<div style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">'
        'Type any Hinglish command below — useful for demos and testing without a mic.'
        '</div>',
        unsafe_allow_html=True,
    )
    demo_examples = [
        "samjhao photosynthesis",
        "quiz lo gravity 3 questions",
        "samjhao water cycle",
        "quiz lo human digestive system 5 questions",
        "batao what is democracy",
    ]

    def _sync_demo_input():
        if st.session_state["demo-select"] != "— pick an example —":
            st.session_state["demo-input"] = st.session_state["demo-select"]

    selected = st.selectbox(
        "Quick examples",
        ["— pick an example —"] + demo_examples,
        key="demo-select",
        on_change=_sync_demo_input,
        label_visibility="collapsed",
    )
    typed = st.text_input(
        "Or type your own command",
        placeholder="e.g. samjhao photosynthesis",
        key="demo-input",
        label_visibility="collapsed",
    )
    if st.button("Use this text", key="btn-demo"):
        if typed.strip():
            st.session_state.last_transcript = typed.strip()
            st.rerun()
        else:
            st.warning("Please type or pick a command first.")



# ── Transcript display ─────────────────────────────────────────────────────────

if st.session_state.last_transcript:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Recognized Text</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="transcript-box">{st.session_state.last_transcript}</div>',
        unsafe_allow_html=True,
    )

    col_gen, col_clear = st.columns([4, 1])
    with col_gen:
        generate_clicked = st.button("Generate — Explain or Quiz", type="primary", key="btn-generate")
    with col_clear:
        if st.button("Clear", key="btn-clear"):
            st.session_state.last_transcript = None
            st.session_state.last_payload = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Generate ──────────────────────────────────────────────────────────────

    if generate_clicked:
        _ensure_api_key()
        with st.spinner("Detecting intent & generating content…"):
            try:
                parsed = detect_intent(st.session_state.last_transcript)

                if parsed.intent == "unknown":
                    st.warning(
                        "**Could not detect intent.** Try phrasing like:\n\n"
                        "- `samjhao photosynthesis` — to explain\n"
                        "- `quiz lo photosynthesis 5 questions` — to quiz"
                    )
                else:
                    st.session_state.last_payload = parsed

                    # ── EXPLAIN ───────────────────────────────────────────────
                    if parsed.intent == "explain":
                        result = explain_concept(parsed.topic)

                        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.markdown('<div class="section-label">Explanation</div>', unsafe_allow_html=True)

                        visual = result.get("visual", {})
                        if visual:
                            st.markdown(
                                f'<div class="result-header">{visual.get("title", parsed.topic)}</div>',
                                unsafe_allow_html=True,
                            )
                            for point in visual.get("points", []):
                                st.markdown(
                                    f'<div class="result-point"><div class="point-dot"></div><div>{point}</div></div>',
                                    unsafe_allow_html=True,
                                )
                            analogy = visual.get("analogy")
                            if analogy:
                                st.markdown(
                                    f'<div class="analogy-box"><span>{analogy}</span></div>',
                                    unsafe_allow_html=True,
                                )

                        speech = result.get("speech", "")
                        if speech:
                            st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
                            st.markdown(
                                f'<div style="color:#94a3b8; font-style:italic; font-size:0.95rem; line-height:1.6">{speech}</div>',
                                unsafe_allow_html=True,
                            )
                            mp3 = synthesize(speech)
                            _play_audio(mp3)

                        st.markdown('</div>', unsafe_allow_html=True)

                    # ── QUIZ ──────────────────────────────────────────────────
                    elif parsed.intent == "quiz":
                        n = parsed.n_questions
                        result = generate_quiz(parsed.topic, n=n)

                        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="section-label">Quiz — {parsed.topic.title()} &nbsp;·&nbsp; {n} Questions</div>',
                            unsafe_allow_html=True,
                        )

                        for i, q in enumerate(result.get("questions", []), start=1):
                            opts_html = "".join(
                                f'<div class="quiz-option">{opt}</div>'
                                for opt in q.get("options", [])
                            )
                            expl = q.get("explanation", "")
                            expl_html = (
                                f'<div style="color:#94a3b8;font-size:0.83rem;margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid rgba(255,255,255,0.05)">{expl}</div>'
                                if expl else ""
                            )
                            st.markdown(f"""
<div class="quiz-card">
    <div class="quiz-num">Q{i}</div>
    <div class="quiz-q">{q.get('q', '')}</div>
    {opts_html}
    <div class="quiz-answer">Answer: {q.get('answer', '')}</div>
    {expl_html}
</div>""", unsafe_allow_html=True)

                            speech = q.get("speech")
                            if speech:
                                mp3 = synthesize(speech)
                                _play_audio(mp3)

                        st.markdown('</div>', unsafe_allow_html=True)

            except ConnectionError as e:
                st.error(f"**Ollama not reachable.**\n\n{e}")
            except Exception as e:
                st.error(f"**Something went wrong:** {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; margin-top:3rem; color:#1e293b; font-size:0.8rem;">
    AuralLearn · Powered by Hugging Face · No data stored
</div>
""", unsafe_allow_html=True)
