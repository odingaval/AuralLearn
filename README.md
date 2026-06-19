# 🎧 AuralLearn

AuralLearn is an **audio-first classroom assistant** built for government schools in Haryana. It lets teachers speak in Hindi or Hinglish to instantly explain concepts or generate quizzes — all running **100% offline** on a local machine, with no API keys or internet required.

## How It Works

```
🎤 Speak (Hindi/Hinglish)
      ↓
📝 Speech-to-Text (browser mic)
      ↓
🧠 Intent detection → EXPLAIN or QUIZ
      ↓
✨ Local LLM (Ollama) generates Hinglish response
      ↓
🔊 Text-to-Speech reads the answer aloud
```

## Features

- **Live Concept Simplification** — say `samjhao photosynthesis` and get a simple Hinglish explanation with bullet points and an Indian analogy
- **Voice-Triggered Quizzing** — say `quiz lo gravity 5 questions` and get 5 MCQs with answers and explanations
- **Fully Offline** — powered by [Ollama](https://ollama.com) running a local 2B model (no Anthropic/OpenAI key needed)
- **Hinglish UI** — designed for grades 6–10, with natural Hindi–English mix in all responses
- **Audio playback** — responses are read aloud via `edge-tts`

## Project Structure

```
AuralLearn/
├── app.py                  # Streamlit entry point (UI orchestration)
├── requirements.txt
└── modules/
    ├── intent.py           # Detects EXPLAIN vs QUIZ intent from Hinglish speech
    ├── llm.py              # Ollama local LLM integration (explain + quiz generation)
    ├── stt.py              # Speech-to-Text via browser Web Speech API + Whisper fallback
    └── tts.py              # Text-to-Speech via edge-tts (gTTS fallback)
```

## Getting Started

### 1. Install Ollama and pull a model

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the 2B model (or any model you prefer)
ollama pull gemma3:2b
```

### 2. Clone and set up the project

```bash
git clone https://github.com/odingaval/AuralLearn.git
cd AuralLearn

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. (Optional) Configure your model

By default the app uses `gemma3:2b`. To use a different model, add a `.env` file:

```bash
# .env
OLLAMA_MODEL=llama3.2:1b        # or any model from `ollama list`
OPENAI_API_KEY=sk-...           # only needed for the Whisper audio upload tab
```

### 4. Run the app

```bash
# Terminal 1 — start Ollama
ollama serve

# Terminal 2 — start the app
source venv/bin/activate
streamlit run app.py
```

Open **http://localhost:8501** in Chrome or Edge.

## Usage Examples

| You say... | App does... |
|---|---|
| `samjhao photosynthesis` | Explains photosynthesis in Hinglish with bullet points and an analogy |
| `what is gravity` | Explains gravity in simple terms |
| `quiz lo photosynthesis 5 questions` | Generates 5 MCQs on photosynthesis |
| `3 sawal pucho gravity pe` | Generates 3 MCQs on gravity |

> **Note:** The microphone tab works best in **Chrome or Edge**. Firefox does not support the Web Speech API. Use the "Upload Audio" tab as a fallback.

## Module Details

### `modules/intent.py`
- Detects intent (`explain` vs `quiz`) using Hinglish keyword matching
- Extracts topic and number of questions (`n_questions`, default 5, capped at 10)

### `modules/llm.py`
- Calls the local Ollama server via the `ollama` Python library
- Uses structured JSON prompts to ensure consistent output format
- Gracefully raises a `ConnectionError` if Ollama is not running

### `modules/stt.py`
- **Primary:** Browser Web Speech API injected via Streamlit HTML component (`lang='hi-IN'`)
- **Fallback:** OpenAI Whisper API for uploaded WAV/MP3/M4A files

### `modules/tts.py`
- **Primary:** `edge-tts` (Hindi voice, generates MP3)
- **Fallback:** `gTTS`

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `ollama` | Local LLM client (replaces Anthropic) |
| `edge-tts` | Primary TTS engine |
| `gTTS` | TTS fallback |
| `openai` | Whisper audio upload fallback only |
| `python-dotenv` | Load `.env` config |

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Chrome or Edge browser (for microphone STT)
- Any Ollama-compatible model installed (e.g. `gemma3:2b`, `llama3.2:1b`)
