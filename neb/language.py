"""Language mapping between EPUB dc:language tags and pocket-tts models."""

from __future__ import annotations

from typing import Optional

POCKET_TTS_LANGUAGES = {
    "english",
    "french",
    "german",
    "italian",
    "portuguese",
    "spanish",
}

DEFAULT_LANGUAGE = "english"

_ISO_TO_POCKET_TTS = {
    "en": "english",
    "eng": "english",
    "fr": "french",
    "fra": "french",
    "fre": "french",
    "de": "german",
    "deu": "german",
    "ger": "german",
    "it": "italian",
    "ita": "italian",
    "pt": "portuguese",
    "por": "portuguese",
    "es": "spanish",
    "spa": "spanish",
}

_DISPLAY_NAMES = {
    "english": "English",
    "french": "French",
    "german": "German",
    "italian": "Italian",
    "portuguese": "Portuguese",
    "spanish": "Spanish",
}


class UnsupportedLanguageError(ValueError):
    """The EPUB declares a language pocket-tts cannot synthesize."""


def normalize_language_tag(tag: Optional[str]) -> str:
    """Map a raw dc:language tag to a pocket-tts language name.

    Empty/missing inputs fall back to DEFAULT_LANGUAGE.
    Raises UnsupportedLanguageError for codes outside pocket-tts' six languages.
    """
    if not tag:
        return DEFAULT_LANGUAGE

    raw = str(tag).strip().lower()
    if not raw:
        return DEFAULT_LANGUAGE

    if raw in POCKET_TTS_LANGUAGES:
        return raw

    primary = raw.replace("_", "-").split("-", 1)[0]
    mapped = _ISO_TO_POCKET_TTS.get(primary)
    if mapped:
        return mapped

    supported = ", ".join(sorted(POCKET_TTS_LANGUAGES))
    raise UnsupportedLanguageError(
        f"Language {tag!r} is not supported by pocket-tts. Supported: {supported}."
    )


def display_name(pocket_tts_language: Optional[str]) -> str:
    """Human-readable name for a pocket-tts language (e.g. 'german' -> 'German')."""
    if not pocket_tts_language:
        return ""
    return _DISPLAY_NAMES.get(
        pocket_tts_language, str(pocket_tts_language).capitalize()
    )
