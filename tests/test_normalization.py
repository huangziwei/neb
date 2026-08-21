"""Cross-language tests for the shared normalization engine.

Per-language depth lives in the language test modules; this file covers the
behaviour every profile is supposed to share, and the smoke coverage for the
four languages added alongside English and German.
"""
from __future__ import annotations

import pytest

from neb.text import prepare_tts_text, profile_for
from neb.text.common import fold_script


def norm(text: str, language: str = "english") -> str:
    return prepare_tts_text(text, language=language)


# ---------------------------------------------------------------------------
# Currency and magnitude word order
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        # A magnitude word belongs between the amount and the currency noun.
        ("$1 billion", "one billion dollars"),
        ("$1 million", "one million dollars"),
        ("$3.5 billion", "three point five billion dollars"),
        ("$20 million in funding", "twenty million dollars in funding"),
        ("£4 million", "four million pounds"),
        ("€2 billion", "two billion euros"),
        ("It cost $1.2 trillion", "It cost one point two trillion dollars"),
        # Attached abbreviations count only against a currency symbol.
        ("$100k", "one hundred thousand dollars"),
        ("$5m", "five million dollars"),
        ("$1bn", "one billion dollars"),
        ("$2 bn", "two billion dollars"),
    ],
)
def test_currency_scale_precedes_the_noun(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$1", "one dollar"),
        ("$5", "five dollars"),
        ("$1.00", "one dollar"),
        ("$1.50", "one point five zero dollars"),
    ],
)
def test_currency_singular_only_for_exactly_one(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


@pytest.mark.parametrize(
    "text, expected",
    [
        # A bare single letter is a unit, not a magnitude — only "$20m" is millions.
        ("20 m", "twenty m"),
        ("5 k", "five k"),
        ("20 million people", "twenty million people"),
    ],
)
def test_bare_letter_is_not_a_magnitude(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


# ---------------------------------------------------------------------------
# Script folding
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "language, text",
    [
        ("german", "Die Äpfel für Herrn Müller sind größer"),
        ("italian", "perché la città è così"),
        ("french", "à côté de l'élève français"),
        ("spanish", "el señor Muñoz de Alcalá"),
        ("portuguese", "o coração de São Paulo, avô"),
    ],
)
def test_native_diacritics_survive(language: str, text: str) -> None:
    assert norm(text, language) == f"{text}."


def test_english_still_transliterates_pali() -> None:
    # English owns no diacritics, so the Pali/Sanskrit spelling-out still runs.
    assert norm("dhammā and saṃsāra") == "dhammaa and samsaara."


def test_fold_script_keeps_only_the_declared_letters() -> None:
    german = profile_for("german")
    # An umlaut is German; an enye is not, and folds away.
    assert fold_script("Müller", german.native_letters) == "Müller"
    assert fold_script("Niño", german.native_letters) == "Nino"
    # With nothing declared native, every mark is stripped.
    assert fold_script("Müller") == "Muller"


def test_unknown_language_falls_back_to_english() -> None:
    assert profile_for("klingon").name == "english"
    assert profile_for(None).name == "english"


# ---------------------------------------------------------------------------
# Symbols
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("50%", "fifty percent"),
        ("3.5%", "three point five percent"),
        ("a 20% raise", "a twenty percent raise"),
        ("40°C", "forty degrees Celsius"),
        ("1°", "one degree"),
        ("5 × 3", "five times three"),
        ("2 + 2 = 4", "two plus two equals four"),
        ("fish & chips", "fish and chips"),
    ],
)
def test_symbols_are_spoken(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


def test_ampersand_inside_a_word_is_left_alone() -> None:
    # "AT&T" is a name, not a conjunction.
    assert norm("AT&T and R&D") == "AT&T and R&D."


# ---------------------------------------------------------------------------
# Fractions and clock times
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("1/2 cup", "one half cup"),
        ("2/3", "two thirds"),
        ("3/4", "three quarters"),
        ("1½ cups", "one and one half cups"),
        ("½", "one half"),
    ],
)
def test_proper_fractions_are_spoken(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


@pytest.mark.parametrize("text", ["24/7", "9/11", "3/4/2020"])
def test_improper_and_date_like_slashes_are_left_alone(text: str) -> None:
    # An idiom or a date is not a quantity; only a proper fraction converts.
    assert "half" not in norm(text)
    assert "quarter" not in norm(text)
    assert "seventh" not in norm(text)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("at 5:30", "at five thirty"),
        ("9:45", "nine forty five"),
        ("5:05", "five oh five"),
        # A scripture reference reads the same way.
        ("John 3:16", "John three sixteen"),
    ],
)
def test_clock_colon_becomes_speakable(text: str, expected: str) -> None:
    assert norm(text) == f"{expected}."


# ---------------------------------------------------------------------------
# The four languages added with the shared engine
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "language, text, expected",
    [
        ("italian", "Capitolo 5", "Capitolo cinque"),
        ("italian", "Nel 1492", "Nel millequattrocentonovantadue"),
        ("italian", "il 3% degli italiani", "il tre per cento degli italiani"),
        ("italian", "Capitolo IV", "Capitolo quattro"),
        ("italian", "1º maggio", "primo maggio"),
        ("italian", "a.C.", "avanti Cristo"),
        ("french", "Chapitre 5", "Chapitre cinq"),
        ("french", "En 1492", "En mille quatre cent quatre-vingt-douze"),
        ("french", "1 500 euros", "mille cinq cents euros"),
        ("french", "1er mai", "premier mai"),
        ("french", "M. Dupont", "Monsieur Dupont"),
        ("french", "av. J.-C.", "avant Jésus-Christ"),
        ("spanish", "Capítulo 5", "Capítulo cinco"),
        ("spanish", "En 1492", "En mil cuatrocientos noventa y dos"),
        ("spanish", "3ª parte", "tercera parte"),
        ("spanish", "1.500 euros", "mil quinientos euros"),
        ("portuguese", "Capítulo 5", "Capítulo cinco"),
        ("portuguese", "3% dos portugueses", "três por cento dos portugueses"),
        ("portuguese", "1º de maio", "primeiro de maio"),
    ],
)
def test_added_languages(language: str, text: str, expected: str) -> None:
    assert prepare_tts_text(text, language=language) == f"{expected}."


@pytest.mark.parametrize(
    "language, text, expected",
    [
        # Romance languages link a magnitude noun to its unit with a preposition,
        # but the thousand words are numeral adjectives and take none.
        ("italian", "$2 miliardi", "due miliardi di dollari"),
        ("italian", "2 mila euro", "due mila euro"),
        ("french", "$2 milliards", "deux milliards de dollars"),
        ("spanish", "$2 millones", "dos millones de dólares"),
        ("spanish", "2 mil euros", "dos mil euros"),
        ("portuguese", "$2 milhões", "dois milhões de dólares"),
        # English and German join them directly.
        ("english", "$2 billion", "two billion dollars"),
        ("german", "$1 Mrd.", "eine Milliarde Dollar"),
    ],
)
def test_scale_preposition(language: str, text: str, expected: str) -> None:
    assert prepare_tts_text(text, language=language) == f"{expected}."


@pytest.mark.parametrize(
    "language, expected",
    [
        ("italian", "un euro"),
        ("french", "un euro"),
        ("spanish", "un euro"),
        ("portuguese", "um euro"),
        ("german", "ein Euro"),
        ("english", "one euro"),
    ],
)
def test_one_takes_its_pre_nominal_form(language: str, expected: str) -> None:
    assert prepare_tts_text("€1", language=language) == f"{expected}."


def test_french_ordinal_gender() -> None:
    assert prepare_tts_text("1re fois", language="french") == "première fois."
    assert prepare_tts_text("2e étage", language="french") == "deuxième étage."


@pytest.mark.parametrize("language", ["italian", "spanish", "portuguese"])
def test_feminine_ordinal_marker(language: str) -> None:
    masculine = prepare_tts_text("1º", language=language)
    feminine = prepare_tts_text("1ª", language=language)
    assert masculine != feminine
    assert feminine.rstrip(".").endswith("a")
