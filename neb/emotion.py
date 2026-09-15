"""Emotion modes for pocket-tts, expressed as punctuation.

`calm` trades exclamation marks for full stops, `normal` changes nothing.
"""

from __future__ import annotations

# Display order for the player's emotion pills.
EMOTIONS = ("normal", "calm")

DEFAULT_EMOTION = "calm"

_DISPLAY_NAMES = {
    "normal": "Normal",
    "calm": "Calm",
}


def resolve_emotion(value: str | None) -> str:
    """Coerce a raw emotion choice to a supported mode.

    Anything unknown, None included, falls back to DEFAULT_EMOTION.
    """
    if not value:
        return DEFAULT_EMOTION
    candidate = str(value).strip().lower()
    if candidate in EMOTIONS:
        return candidate
    return DEFAULT_EMOTION


def display_name(emotion: str | None) -> str:
    """Human-readable label for an emotion mode (e.g. 'calm' -> 'Calm')."""
    return _DISPLAY_NAMES[resolve_emotion(emotion)]
