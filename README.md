---
title: AuralLearn
emoji: 🎧
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🎧 AuralLearn

AuralLearn is an **audio-first classroom assistant** built for government schools in Haryana. It lets teachers speak in Hindi or Hinglish to instantly explain concepts or generate quizzes — powered by the extremely fast and free Groq API.

## How It Works

```
🎤 Speak (Hindi/Hinglish)
      ↓
📝 Speech-to-Text (browser mic)
      ↓
🧠 Intent detection → EXPLAIN or QUIZ
      ↓
✨ Fast LLM (Groq) generates Hinglish response
      ↓
🔊 Text-to-Speech reads the answer aloud
```

## Features

- **Live Concept Simplification** — say `samjhao photosynthesis` and get a simple Hinglish explanation with bullet points and an Indian analogy
- **Voice-Triggered Quizzing** — say `quiz lo gravity 5 questions` and get 5 MCQs with answers and explanations
- **Extremely Fast** — powered by [Groq](https://groq.com) running Llama 3 models (no Anthropic/OpenAI key needed)
- **Hinglish UI** — designed for grades 6–10, with natural Hindi–English mix in all responses
- **Audio playback** — responses are read aloud via `edge-tts`

## Project Structure

```
AuralLearn/
├── app.py                  # Streamlit entry point (UI orchestration)
├── requirements.txt
└── modules/
    ├── intent.py           # Detects EXPLAIN vs QUIZ intent from Hinglish speech
    ├── llm.py              # Groq API integration (explain + quiz generation)
    ├── stt.py              # Speech-to-Text via browser Web Speech API + Whisper fallback
    └── tts.py              # Text-to-Speech via edge-tts (gTTS fallback)
```

## Getting Started

### 1. Get a Groq API Key

1. Go to [console.groq.com](https://console.groq.com) and sign up for a free account.
2. Generate an API key (starts with `gsk_`).

### 2. Clone and set up the project

```bash
git clone https://github.com/odingaval/AuralLearn.git
cd AuralLearn

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. (Optional) Configure your model

By default the app uses `llama-3.1-8b-instant`. Add your API key in a `.env` file:

```bash
# .env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-8b-instant  # optional, default is already llama-3.1-8b-instant
OPENAI_API_KEY=sk-...            # only needed for the Whisper audio upload tab
```

### 4. Run the app

```bash
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
- Calls the blazing fast Groq server via the `groq` Python library
- Uses structured JSON prompts to ensure consistent output format
- Gracefully handles API rate limits or missing keys

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
| `groq` | Cloud LLM client |
| `edge-tts` | Primary TTS engine |
| `gTTS` | TTS fallback |
| `openai` | Whisper audio upload fallback only |
| `python-dotenv` | Load `.env` config |

## Requirements

- Python 3.10+
- A free [Groq API Key](https://console.groq.com)
- Chrome or Edge browser (for microphone STT)
