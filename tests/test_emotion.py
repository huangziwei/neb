"""Tests for the emotion modes and the punctuation pass they drive."""
from __future__ import annotations

import pytest

from neb import emotion
from neb.text import prepare_tts_text, soften_exclamations


def test_resolve_emotion_accepts_supported_modes() -> None:
    assert emotion.resolve_emotion("normal") == "normal"
    assert emotion.resolve_emotion("calm") == "calm"
    assert emotion.resolve_emotion(" Calm ") == "calm"


def test_resolve_emotion_falls_back_to_default() -> None:
    assert emotion.resolve_emotion(None) == "calm"
    assert emotion.resolve_emotion("") == "calm"
    assert emotion.resolve_emotion("excited") == "calm"
    assert emotion.DEFAULT_EMOTION == "calm"


def test_display_names_cover_every_mode() -> None:
    assert [emotion.display_name(name) for name in emotion.EMOTIONS] == [
        "Normal",
        "Calm",
    ]


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Run!", "Run."),
        ("Run! Hide! Now!", "Run. Hide. Now."),
        ("Stop!!", "Stop."),
        ("Hurry!!!", "Hurry."),
        ("Ah! Ah!!!!", "Ah. Ah."),
        # A question survives the trade; a full stop cannot carry it.
        ("No!?", "No?"),
        ("What'd he do?!", "What'd he do?"),
        # So does a trail-off.
        ("It's worse in Philly!...", "It's worse in Philly..."),
        ("Men kiss calves!…", "Men kiss calves…"),
        # An abbreviation's own period is not doubled up.
        ("P. W.!-I see", "P. W.-I see"),
        ("Nothing to soften here.", "Nothing to soften here."),
    ],
)
def test_soften_exclamations(raw: str, expected: str) -> None:
    assert soften_exclamations(raw) == expected


def test_soften_exclamations_drops_spanish_opener() -> None:
    assert soften_exclamations("¡Hola!") == "Hola."
    assert soften_exclamations("Dijo: ¡Corre!") == "Dijo: Corre."
    # The inverted question mark is untouched — its pair survives.
    assert soften_exclamations("¿Qué pasa?") == "¿Qué pasa?"


def test_prepare_tts_text_softens_by_default() -> None:
    assert prepare_tts_text("Run for your life!") == "Run for your life."


def test_prepare_tts_text_normal_mode_passes_text_through() -> None:
    assert (
        prepare_tts_text("Run for your life!", emotion="normal")
        == "Run for your life!"
    )


def test_prepare_tts_text_calm_mode_is_explicit() -> None:
    assert (
        prepare_tts_text("Run for your life!", emotion="calm")
        == "Run for your life."
    )


def test_prepare_tts_text_softens_after_normalization() -> None:
    # The number normalizer runs first; softening still lands on its output.
    assert (
        prepare_tts_text("I paid $5!", emotion="calm") == "I paid five dollars."
    )


def test_prepare_tts_text_softens_every_language() -> None:
    for language in ("english", "french", "german", "italian", "portuguese", "spanish"):
        assert prepare_tts_text("Hola!", language=language).endswith("Hola.")
