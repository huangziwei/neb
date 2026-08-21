"""Text I/O and TTS-time normalization.

Layout:
  * `io`       — reading clean text and inferring chapter titles
  * `common`   — language-agnostic helpers (strip brackets/quotes, script
                 folding, reading overrides, linebreak pauses)
  * `profile`  — the per-language data record
  * `engine`   — the shared normalization pipeline every language runs
  * `english`, `german`, `italian`, `french`, `spanish`, `portuguese`
               — one profile each, matching pocket-tts' six languages

`prepare_tts_text` picks the profile for the book's language and runs the
common pre-processing steps before handing off to the engine.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from . import engine
from . import english as _english
from . import french as _french
from . import german as _german
from . import italian as _italian
from . import portuguese as _portuguese
from . import spanish as _spanish
from .common import (
    READING_OVERRIDES_FILENAME,
    _normalize_linebreak_pauses,
    _strip_brackets,
    _strip_double_quotes,
    _strip_single_quotes,
    apply_reading_overrides,
    fold_script,
)

# Re-exported for callers that reach for the override plumbing through the
# package root rather than `neb.text.common`.
from .common import _load_reading_overrides as _load_reading_overrides
from .common import _merge_reading_overrides as _merge_reading_overrides
from .english import (
    normalize_abbreviations,
    normalize_english_lexical,
    normalize_numbers_for_tts,
    normalize_urls,
)
from .french import normalize_french_lexical
from .german import normalize_german_lexical
from .io import guess_title_from_path, read_clean_text, title_from_filename
from .italian import normalize_italian_lexical
from .portuguese import normalize_portuguese_lexical
from .profile import LanguageProfile
from .spanish import normalize_spanish_lexical

__all__ = [
    "READING_OVERRIDES_FILENAME",
    "LanguageProfile",
    "apply_reading_overrides",
    "fold_script",
    "guess_title_from_path",
    "normalize_abbreviations",
    "normalize_english_lexical",
    "normalize_french_lexical",
    "normalize_german_lexical",
    "normalize_italian_lexical",
    "normalize_numbers_for_tts",
    "normalize_portuguese_lexical",
    "normalize_spanish_lexical",
    "normalize_urls",
    "prepare_tts_text",
    "profile_for",
    "read_clean_text",
    "title_from_filename",
]


_PROFILES: dict[str, LanguageProfile] = {
    "english": _english.PROFILE,
    "french": _french.PROFILE,
    "german": _german.PROFILE,
    "italian": _italian.PROFILE,
    "portuguese": _portuguese.PROFILE,
    "spanish": _spanish.PROFILE,
}


def profile_for(language: str | None) -> LanguageProfile:
    """Profile for a pocket-tts language name, falling back to English."""
    return _PROFILES.get(str(language or "").lower(), _english.PROFILE)


def prepare_tts_text(
    text: str,
    reading_overrides: Sequence[dict[str, Any]] | None = None,
    language: str = "english",
) -> str:
    profile = profile_for(language)
    overrides = reading_overrides or []
    text = _strip_brackets(text)
    text = _strip_double_quotes(text)
    text = _strip_single_quotes(text)
    text = apply_reading_overrides(text, overrides)
    text = fold_script(text, profile.native_letters, profile.transliterate_indic)
    # Apply reading overrides twice so users can match either original
    # spellings (with diacritics) or folded forms.
    text = apply_reading_overrides(text, overrides)
    text = engine.normalize_lexical(text, profile)
    text = _normalize_linebreak_pauses(text)
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text
