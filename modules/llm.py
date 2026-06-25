"""
llm.py — Groq Inference API integration with Hinglish prompts.
Handles EXPLAIN and QUIZ intent responses using Groq's free-tier API.
Groq is free, extremely fast, and requires no special permissions.
"""

import json
import re
import os
from typing import Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Model config ───────────────────────────────────────────────────────────────

# Free Groq models — llama-3.1-8b-instant is fast and great for JSON output.
# Override via GROQ_MODEL env var.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── System prompts ─────────────────────────────────────────────────────────────

SYSTEM_EXPLAIN = """
You are a classroom teaching assistant for a Haryana government school.
Students are in grades 6-10 and speak Hinglish (Hindi-English mix).

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
Students are in grades 6-10 and speak Hinglish (Hindi-English mix).

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
    raw = re.sub(r"```(?:json)?", "", raw).strip("` \n")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from LLM response:\n{raw}")


# ── Groq chat helper ───────────────────────────────────────────────────────────

def _chat(system_prompt: str, user_msg: str, max_tokens: int = 600) -> str:
    """
    Send a chat request to Groq's free inference API.
    Requires GROQ_API_KEY in .env — get one free at https://console.groq.com
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise PermissionError(
            "GROQ_API_KEY is missing.\n"
            "Get a free key at https://console.groq.com and add it to your .env file:\n"
            "GROQ_API_KEY=gsk_your_key_here"
        )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "invalid api key" in error_str:
            raise PermissionError(
                "Groq API key is invalid. Check GROQ_API_KEY in your .env file."
            ) from e
        if "429" in error_str or "rate limit" in error_str:
            raise RuntimeError(
                "Groq rate limit hit. Wait a moment and try again."
            ) from e
        raise


# ── Public API ─────────────────────────────────────────────────────────────────

def explain_concept(topic: str) -> dict[str, Any]:
    """
    Ask the model to explain a concept in Hinglish.

    Returns dict with keys:
        speech  -> str (Hinglish explanation)
        visual  -> dict (title, points[], analogy)
    """
    user_msg = f"Explain the concept of '{topic}' to grade 6-10 students in Hinglish."
    raw = _chat(SYSTEM_EXPLAIN, user_msg, max_tokens=600)
    return _parse_json(raw)


def generate_quiz(topic: str, n: int = 5) -> dict[str, Any]:
    """
    Ask the model to generate N MCQs on a topic in Hinglish.

    Returns dict with key:
        questions -> list of dicts (q, options[], answer, explanation, speech)
    """
    user_msg = (
        f"Create exactly {n} MCQ questions on the topic '{topic}' "
        f"for grade 6-10 students in Hinglish."
    )
    raw = _chat(SYSTEM_QUIZ, user_msg, max_tokens=2000)
    return _parse_json(raw)
