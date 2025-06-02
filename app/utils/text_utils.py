"""
Text processing utilities
"""
import html
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """Clean and sanitize text input"""
    if not text:
        return ""

    # Remove HTML tags
    text = html.escape(text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix"""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation)"""
    # Remove punctuation and convert to lowercase
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

    # Remove common stop words
    stop_words = {
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "this",
        "that",
        "these",
        "those",
        "they",
        "them",
        "their",
        "there",
        "where",
        "when",
        "why",
        "how",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "have",
        "has",
        "had",
        "are",
        "was",
        "were",
        "been",
        "being",
    }

    # Filter out stop words and get unique keywords
    keywords = list(set(word for word in words if word not in stop_words))

    # Sort by length (longer words often more meaningful)
    keywords.sort(key=len, reverse=True)

    return keywords[:max_keywords]


def format_dialogue(character: str, text: str) -> str:
    """Format dialogue with character name"""
    return f"{character}: {text}"


def parse_dialogue(dialogue_text: str) -> Optional[tuple]:
    """Parse dialogue text to extract character and text"""
    if ":" in dialogue_text:
        parts = dialogue_text.split(":", 1)
        if len(parts) == 2:
            character = parts[0].strip()
            text = parts[1].strip()
            return character, text

    return None


def word_count(text: str) -> int:
    """Count words in text"""
    return len(re.findall(r"\b\w+\b", text))


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time in seconds"""
    words = word_count(text)
    minutes = words / words_per_minute
    return int(minutes * 60)
