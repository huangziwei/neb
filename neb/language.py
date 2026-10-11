"""Language mapping between EPUB dc:language tags and pocket-tts models."""

from __future__ import annotations

POCKET_TTS_LANGUAGES = {
    "english",
    "french",
    "german",
    "italian",
    "portuguese",
    "spanish",
}

DEFAULT_LANGUAGE = "english"

_POCKET_TTS_MODEL_IDS: dict[tuple[str, int], str] = {
    ("english", 6): "english",
    ("french", 24): "french_24l",
    ("german", 6): "german",
    ("german", 24): "german_24l",
    ("italian", 6): "italian",
    ("italian", 24): "italian_24l",
    ("portuguese", 6): "portuguese",
    ("portuguese", 24): "portuguese_24l",
    ("spanish", 6): "spanish",
    ("spanish", 24): "spanish_24l",
}

_DEFAULT_LAYERS_BY_LANGUAGE: dict[str, int] = {
    "english": 6,
    "french": 24,
    "german": 24,
    "italian": 6,
    "portuguese": 6,
    "spanish": 24,
}

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


def normalize_language_tag(tag: str | None) -> str:
    """Map a dc:language tag to a pocket-tts language name, raising if unsupported."""
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


def display_name(pocket_tts_language: str | None) -> str:
    if not pocket_tts_language:
        return ""
    return _DISPLAY_NAMES.get(
        pocket_tts_language, str(pocket_tts_language).capitalize()
    )


def resolve_language(tag: str | None) -> str:
    try:
        return normalize_language_tag(tag)
    except UnsupportedLanguageError:
        return DEFAULT_LANGUAGE


def available_layers(language: str) -> list[int]:
    lang = resolve_language(language)
    return sorted({layers for (lng, layers) in _POCKET_TTS_MODEL_IDS if lng == lang})


def default_layers(language: str) -> int:
    """Upstream-recommended layer count for a language."""
    lang = resolve_language(language)
    return _DEFAULT_LAYERS_BY_LANGUAGE.get(lang, 6)


def resolve_layers(language: str, layers: int | None) -> int:
    lang = resolve_language(language)
    options = available_layers(lang)
    if layers in options:
        return int(layers)
    return default_layers(lang)


def resolve_model_id(language: str, layers: int | None = None) -> str:
    """Return the pocket-tts YAML stem for a (language, layers) pair."""
    lang = resolve_language(language)
    lay = resolve_layers(lang, layers)
    model_id = _POCKET_TTS_MODEL_IDS.get((lang, lay))
    if model_id is None:
        model_id = _POCKET_TTS_MODEL_IDS[(lang, default_layers(lang))]
    return model_id


# pocket-tts model id -> maneko config stem; identical except for English.
_POCKET_ID_TO_MANEKO_STEM: dict[str, str] = {
    "english": "english_2026-04",
}


def resolve_maneko_language(language: str, layers: int | None = None) -> str:
    """Return the maneko config stem for a (language, layers) pair."""
    model_id = resolve_model_id(language, layers)
    return _POCKET_ID_TO_MANEKO_STEM.get(model_id, model_id)
