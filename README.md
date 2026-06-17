# AuralLearn (Prototype)

AuralLearn is a small prototype for an **audio-first classroom assistant**:

- Teachers speak a command (Hindi/Hinglish)
- The app detects whether the teacher wants an **EXPLAIN** or a **QUIZ**
- A Claude/LLM backend generates either:
  - a short Hinglish explanation + simple visual bullets
  - or an MCQ quiz (exactly *N* questions)
- The app can read results back using Text-to-Speech (TTS)

> Current repo status: this folder contains **module code only** (`modules/`). There is **no Streamlit app entrypoint** (e.g., `app.py` / `streamlit_app.py`) in the repo root.

## Project Structure

- `modules/intent.py` – Detects intent (`explain` vs `quiz`) and extracts topic + number of questions
- `modules/llm.py` – Anthropic Claude integration to produce JSON for explanation/quiz
- `modules/stt.py` – Speech-to-Text using browser Web Speech API (with a Whisper fallback)
- `modules/tts.py` – TTS using `edge-tts` (with `gTTS` fallback)
- `assets/` – placeholder for future static assets

## Capabilities (by module)

### 1) Intent detection (`modules/intent.py`)
- Supports Hindi/Hinglish keywords
- Quiz mode keyword examples: `quiz lo`, `MCQ`, `sawal`, `test karo`
- Explain mode keyword examples: `samjhao`, `batao`, `concept`, `what is`
- Extracts:
  - `topic` (remaining text after removing trigger words)
  - `n_questions` (defaults to 5, capped at 10)

### 2) LLM output formatting (`modules/llm.py`)
Uses Anthropic Claude and forces **ONLY valid JSON** responses.

- `explain_concept(topic)` returns:
  - `speech`: Hinglish explanation (<= 80 words)
  - `visual`: title, emoji, bullet points, and a one-line analogy

- `generate_quiz(topic, n)` returns:
  - `questions`: a list of MCQs with:
    - `q`, `options` (A/B/C/D labeled), `answer`, `explanation`, `speech`

### 3) Speech-to-Text (`modules/stt.py`)
- Primary: browser **Web Speech API** via Streamlit HTML injection
  - Uses `lang='hi-IN'`
- Fallback: OpenAI **Whisper** for uploaded audio

### 4) Text-to-Speech (`modules/tts.py`)
- Primary: `edge-tts` to generate MP3 (Hindi voice by default)
- Fallback: `gTTS`

## Environment Variables

### Anthropic
`modules/llm.py` requires:
- `ANTHROPIC_API_KEY`

### OpenAI (only if Whisper fallback is used)
`modules/stt.py` expects an OpenAI API key passed into `transcribe_with_whisper(...)`.

## Dependencies

This repo currently does not ship a `requirements.txt` or similar manifest.
Based on the modules, you’ll likely need:
- `streamlit` (for `stt.py`)
- `anthropic` (for `llm.py`)
- `edge-tts` (for `tts.py`)
- `gTTS` (fallback for `tts.py`)
- `openai` (for Whisper fallback in `stt.py`)

## How to run (what’s missing)

To turn this into a runnable application, you need to add a Streamlit entry file such as:

- `app.py`

And wire together the flow:
1. Render STT UI (`render_browser_stt()`)
2. Detect intent (`detect_intent(transcript)`)
3. Call LLM:
   - `explain_concept(topic)` or `generate_quiz(topic, n_questions)`
4. Convert returned `speech` to audio (`tts.synthesize(...)`)

## Notes / Limitations

- The current repository contains only modules; **no UI orchestration** exists yet.
- LLM/TTS/STT parts require external services and packages.
- `llm.py` is strict about returning valid JSON; if the model ever includes extra text, `_parse_json` attempts to recover.

## Next steps (now that it’s wired)

- Install dependencies: `pip install -r requirements.txt`
- Set `ANTHROPIC_API_KEY` in your environment
- Run: `streamlit run app.py`

## Notes

This repo previously contained only modules. It now includes a basic Streamlit `app.py` that connects:
- `modules/stt.py` (STT UI)
- `modules/intent.py` (intent detection)
- `modules/llm.py` (Claude generation)
- `modules/tts.py` (audio playback)


