"""
llm.py — Claude API integration with Hinglish prompts.
Handles EXPLAIN and QUIZ intent responses.
"""

import json
import re
import os
import anthropic
from typing import Any

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
    "emoji": "<single relevant emoji>",
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


# ── Client ─────────────────────────────────────────────────────────────────────

def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file or environment."
        )
    return anthropic.Anthropic(api_key=api_key)


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


# ── Public API ─────────────────────────────────────────────────────────────────

def explain_concept(topic: str) -> dict[str, Any]:
    """
    Ask Claude to explain a concept in Hinglish.

    Returns dict with keys:
        speech  → str (Hinglish explanation)
        visual  → dict (title, emoji, points[], analogy)
    """
    client = _get_client()
    user_msg = f"Explain the concept of '{topic}' to grade 6-10 students in Hinglish."

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        system=SYSTEM_EXPLAIN,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text
    return _parse_json(raw)


def generate_quiz(topic: str, n: int = 5) -> dict[str, Any]:
    """
    Ask Claude to generate N MCQs on a topic in Hinglish.

    Returns dict with key:
        questions → list of dicts (q, options[], answer, explanation, speech)
    """
    client = _get_client()
    user_msg = (
        f"Create exactly {n} MCQ questions on the topic '{topic}' "
        f"for grade 6-10 students in Hinglish."
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_QUIZ,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text
    return _parse_json(raw)
