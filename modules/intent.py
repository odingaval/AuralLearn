"""
intent.py — Classify teacher's spoken command into EXPLAIN or QUIZ mode.
Supports Hinglish (Hindi + English) keywords for both explain and quiz triggers.
"""

import re
from dataclasses import dataclass
from typing import Literal

Intent = Literal["explain", "quiz", "unknown"]


EXPLAIN_KEYWORDS = [
    # Hinglish / Hindi
    "samjhao", "samjha", "batao", "bata", "explain", "samjhaiye",
    "padhao", "padhiye", "concept", "kya hai", "matlab", "definition",
    "describe", "batayein", "clear karo", "clear kar",
    # English
    "what is", "tell me about", "describe", "introduce", "overview",
]

QUIZ_KEYWORDS = [
    # Hinglish / Hindi
    "quiz lo", "quiz", "sawal", "sawal pucho", "questions", "test lo",
    "test karo", "test the students", "exam", "check karo", "pucho",
    "MCQ", "mcq", "sawaal", "pariksha",
    # English
    "ask questions", "quiz time", "test students", "question",
]


@dataclass
class ParsedIntent:
    intent: Intent
    topic: str
    n_questions: int = 5  # default question count for quiz mode


def _extract_topic(text: str) -> str:
    """
    Remove intent-trigger words and return the remaining topic phrase.
    """
    clean = text.lower()
    all_triggers = EXPLAIN_KEYWORDS + QUIZ_KEYWORDS + [
        "bachon ko", "students ko", "easy tareeke se", "pe", "par",
        "ka", "ki", "ke", "ko", "mein", "se", "aur", "please",
    ]
    for kw in sorted(all_triggers, key=len, reverse=True):
        clean = re.sub(rf"\b{re.escape(kw)}\b", " ", clean, flags=re.IGNORECASE)

    # Strip numeric phrases like "5 questions ka"
    clean = re.sub(r"\d+\s*(questions?|sawal|sawaal|mcq)", " ", clean, flags=re.IGNORECASE)
    topic = " ".join(clean.split()).strip(" ,.!?")
    return topic if topic else "the given topic"


def _extract_n_questions(text: str) -> int:
    """Pull a number like '5 questions' from the text."""
    match = re.search(r"(\d+)\s*(questions?|sawal|sawaal|MCQ|mcq)", text, re.IGNORECASE)
    if match:
        return min(int(match.group(1)), 10)  # cap at 10
    return 5


def detect_intent(text: str) -> ParsedIntent:
    """
    Returns ParsedIntent with intent label + extracted topic (+ n_questions for quiz).

    Examples:
        "Photosynthesis samjhao bachon ko"  → explain, topic="photosynthesis"
        "5 questions ka quiz lo photosynthesis pe" → quiz, topic="photosynthesis", n=5
    """
    lower = text.lower()

    # Check quiz first (more specific)
    for kw in QUIZ_KEYWORDS:
        if kw in lower:
            return ParsedIntent(
                intent="quiz",
                topic=_extract_topic(text),
                n_questions=_extract_n_questions(text),
            )

    # Check explain
    for kw in EXPLAIN_KEYWORDS:
        if kw in lower:
            return ParsedIntent(
                intent="explain",
                topic=_extract_topic(text),
            )

    return ParsedIntent(intent="unknown", topic=_extract_topic(text))
