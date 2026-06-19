"""
llm.py — Ollama local LLM integration with Hinglish prompts.
Handles EXPLAIN and QUIZ intent responses using a locally running model.
"""

import json
import re
import os
from typing import Any
import ollama

# ── Model config ───────────────────────────────────────────────────────────────

# Change this to match whatever model you have installed (run `ollama list`)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:2b")

# ── System prompts ─────────────────────────────────────────────────────────────

SYSTEM_EXPLAIN = """
You are a classroom teaching assistant for a Haryana government school.
Students are in grades 6–10 and speak Hinglish (Hindi–English mix).

When asked to explain a concept:
- Respond in natural Hinglish (mix Hindi and English naturally)
- Use simple, relatable Indian examples: farming, cricket, food, Diwali, etc.
- Keep explanation under 80 words
- Use short sentences; avoid jargon

Output ONLY valid JSON (no extra text, no markdown):
{
  "speech": "<Hinglish explanation to be read aloud>",
  "visual": {
    "title": "<short topic title>",
    "points": ["<point 1>", "<point 2>", "<point 3>"],
    "analogy": "<one-line relatable Indian analogy>"
  }
}
""".strip()

SYSTEM_QUIZ = """
You are a classroom teaching assistant for a Haryana government school.
Students are in grades 6–10 and speak Hinglish (Hindi–English mix).

When asked to create a quiz:
- Generate exactly N MCQ questions on the given topic
- Questions and options should be in Hinglish
- Each question must have exactly 4 options labeled A, B, C, D
- Vary difficulty: mix easy, medium, and one tricky question

Output ONLY valid JSON (no extra text, no markdown):
{
  "questions": [
    {
      "q": "<question text in Hinglish>",
      "options": ["A. <text>", "B. <text>", "C. <text>", "D. <text>"],
      "answer": "<correct option letter, e.g. B>",
      "explanation": "<brief Hinglish explanation of why this is correct>",
      "speech": "<how TTS should read this question aloud>"
    }
  ]
}
""".strip()


# ── JSON parser ────────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict[str, Any]:
    """
    Robustly extract and parse JSON from LLM response.
    Handles extra whitespace, markdown fences, etc.
    """
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip("` \n")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from LLM response:\n{raw}")


# ── Ollama call helper ─────────────────────────────────────────────────────────

def _chat(system_prompt: str, user_msg: str, max_tokens: int = 600) -> str:
    """
    Send a chat request to the local Ollama server.
    Raises a clear error if Ollama is not running.
    """
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            options={"num_predict": max_tokens},
        )
        return response["message"]["content"]
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "refused" in error_str:
            raise ConnectionError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  ollama serve\n"
                f"Then check your model is installed: ollama list\n"
                f"Current model: {OLLAMA_MODEL}"
            ) from e
        raise


# ── Public API ─────────────────────────────────────────────────────────────────

def explain_concept(topic: str) -> dict[str, Any]:
    """
    Ask the local model to explain a concept in Hinglish.

    Returns dict with keys:
        speech  → str (Hinglish explanation)
        visual  → dict (title, points[], analogy)
    """
    user_msg = f"Explain the concept of '{topic}' to grade 6-10 students in Hinglish."
    raw = _chat(SYSTEM_EXPLAIN, user_msg, max_tokens=600)
    return _parse_json(raw)


def generate_quiz(topic: str, n: int = 5) -> dict[str, Any]:
    """
    Ask the local model to generate N MCQs on a topic in Hinglish.

    Returns dict with key:
        questions → list of dicts (q, options[], answer, explanation, speech)
    """
    user_msg = (
        f"Create exactly {n} MCQ questions on the topic '{topic}' "
        f"for grade 6-10 students in Hinglish."
    )
    raw = _chat(SYSTEM_QUIZ, user_msg, max_tokens=2000)
    return _parse_json(raw)
