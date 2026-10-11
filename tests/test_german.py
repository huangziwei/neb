"""Unit and integration tests for the German TTS normalizer."""
from __future__ import annotations

import pytest

from neb.text import german, prepare_tts_text

# --- _int_to_words — cardinals -----------------------------------------------

@pytest.mark.parametrize(
    "value, expected",
    [
        (0, "null"),
        (1, "eins"),
        (2, "zwei"),
        (9, "neun"),
        (10, "zehn"),
        (11, "elf"),
        (12, "zwölf"),
        (13, "dreizehn"),
        (16, "sechzehn"),
        (17, "siebzehn"),
        (19, "neunzehn"),
        (20, "zwanzig"),
        (21, "einundzwanzig"),
        (22, "zweiundzwanzig"),
        (30, "dreißig"),
        (41, "einundvierzig"),
        (67, "siebenundsechzig"),
        (99, "neunundneunzig"),
        (100, "einhundert"),
        (101, "einhunderteins"),
        (121, "einhunderteinundzwanzig"),
        (200, "zweihundert"),
        (999, "neunhundertneunundneunzig"),
        (1000, "eintausend"),
        (1001, "eintausendeins"),
        (1985, "eintausendneunhundertfünfundachtzig"),
        (10_000, "zehntausend"),
        (100_000, "einhunderttausend"),
        (999_999, "neunhundertneunundneunzigtausendneunhundertneunundneunzig"),
        (1_000_000, "eine Million"),
        (2_000_000, "zwei Millionen"),
        (1_500_000, "eine Million fünfhunderttausend"),
        (1_000_000_000, "eine Milliarde"),
        (3_000_000_000, "drei Milliarden"),
        (1_000_000_000_000, "eine Billion"),
    ],
)
def test_int_to_words(value: int, expected: str) -> None:
    assert german._int_to_words(value) == expected


def test_int_to_words_negative() -> None:
    assert german._int_to_words(-5) == "minus fünf"


# --- _year_to_words ----------------------------------------------------------

@pytest.mark.parametrize(
    "year, expected",
    [
        (1100, "elfhundert"),
        (1492, "vierzehnhundertzweiundneunzig"),
        (1900, "neunzehnhundert"),
        (1901, "neunzehnhunderteins"),
        (1985, "neunzehnhundertfünfundachtzig"),
        (1999, "neunzehnhundertneunundneunzig"),
        (2000, "zweitausend"),
        (2001, "zweitausendeins"),
        (2020, "zweitausendzwanzig"),
        (2099, "zweitausendneunundneunzig"),
    ],
)
def test_year_to_words(year: int, expected: str) -> None:
    assert german._year_to_words(year) == expected


def test_year_to_words_out_of_range_falls_back() -> None:
    # Years outside 1100-2099 use the plain integer form.
    assert german._year_to_words(42) == "zweiundvierzig"


# --- _int_to_ordinal_words ---------------------------------------------------

@pytest.mark.parametrize(
    "value, expected",
    [
        (1, "erste"),
        (2, "zweite"),
        (3, "dritte"),
        (4, "vierte"),
        (5, "fünfte"),
        (6, "sechste"),
        (7, "siebte"),
        (8, "achte"),
        (9, "neunte"),
        (10, "zehnte"),
        (11, "elfte"),
        (12, "zwölfte"),
        (19, "neunzehnte"),
        (20, "zwanzigste"),
        (21, "einundzwanzigste"),
        (23, "dreiundzwanzigste"),
        (100, "hundertste"),
        (102, "einhundertzweite"),
        (110, "einhundertzehnte"),
    ],
)
def test_int_to_ordinal_words(value: int, expected: str) -> None:
    assert german._int_to_ordinal_words(value) == expected


# --- Abbreviations -----------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("z. B. Äpfel", "zum Beispiel Äpfel"),
        ("z.B. Äpfel", "zum Beispiel Äpfel"),
        ("d. h. sofort", "das heißt sofort"),
        ("u. a. das Buch", "unter anderem das Buch"),
        ("s. o. Kapitel", "siehe oben Kapitel"),
        ("v. a. morgens", "vor allem morgens"),
    ],
)
def test_multi_dot_abbreviations(text: str, expected: str) -> None:
    assert german.normalize_abbreviations(text) == expected


def test_dr_prof_expand_to_full_word() -> None:
    assert (
        german.normalize_abbreviations("Dr. Müller und Prof. Schmidt")
        == "Doktor Müller und Professor Schmidt"
    )


def test_nr_abbreviation_expands_before_digit() -> None:
    assert german.normalize_abbreviations("Nr. 7 Tickets") == "Nummer 7 Tickets"


def test_seite_abbreviation_expands_before_digit() -> None:
    assert german.normalize_abbreviations("vgl. S. 42") == "vergleiche Seite 42"


def test_seite_abbreviation_expands_before_roman_numeral() -> None:
    assert german.normalize_abbreviations("vgl. S. XII") == "vergleiche Seite XII"


def test_bzw_usw_ca_expand() -> None:
    assert (
        german.normalize_abbreviations("Äpfel bzw. Birnen usw. ca. 5 Stück")
        == "Äpfel beziehungsweise Birnen und so weiter circa 5 Stück"
    )


# --- Currency ----------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Das kostet €50.", "Das kostet fünfzig Euro."),
        # "eins Euro" is wrong; the numeral takes its pre-nominal form.
        ("Nur 1€ pro Stück.", "Nur ein Euro pro Stück."),
        ("Ungefähr $500 pro Monat.", "Ungefähr fünfhundert Dollar pro Monat."),
        ("Der Preis war £20.", "Der Preis war zwanzig Pfund."),
        # dot as thousands separator
        ("€1.000 im Jahr.", "eintausend Euro im Jahr."),
        # comma as decimal separator
        ("€2,50 kostet", "zwei Komma fünf null Euro kostet"),
    ],
)
def test_normalize_currency_symbols(text: str, expected: str) -> None:
    assert german._normalize_currency_symbols(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        # A magnitude word belongs between the amount and the currency noun.
        ("$1 Mrd.", "eine Milliarde Dollar"),
        ("5 Mio. Euro", "fünf Millionen Euro"),
        ("€2 Milliarden", "zwei Milliarden Euro"),
        ("1 Mio.", "eine Million"),
    ],
)
def test_currency_and_scale_word_order(text: str, expected: str) -> None:
    assert prepare_tts_text(text, language="german") == f"{expected}."


@pytest.mark.parametrize(
    "text, expected",
    [
        # A price is not a year, so it keeps its cardinal reading.
        ("1500 Euro", "eintausendfünfhundert Euro"),
        ("1500 Menschen", "eintausendfünfhundert Menschen"),
        ("im Jahr 1500", "im Jahr fünfzehnhundert"),
    ],
)
def test_quantity_beats_year_reading(text: str, expected: str) -> None:
    assert prepare_tts_text(text, language="german") == f"{expected}."


def test_currency_no_plural_s() -> None:
    # German Euro, Dollar and Pfund keep the singular form in the plural.
    assert "Euros" not in german._normalize_currency_symbols("€10")
    assert "Dollars" not in german._normalize_currency_symbols("$5")


# --- Era markers -------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("500 v. Chr.", "500 vor Christus"),
        ("500 v.Chr.", "500 vor Christus"),
        ("70 n. Chr. war", "70 nach Christus war"),
        ("500 v. u. Z.", "500 vor unserer Zeitrechnung"),
        ("70 n.u.Z.", "70 nach unserer Zeitrechnung"),
    ],
)
def test_normalize_era_abbreviations(text: str, expected: str) -> None:
    assert german._normalize_era_abbreviations(text) == expected


# --- Roman numerals ----------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Kapitel V", "Kapitel fünf"),
        ("Kapitel IV und V", "Kapitel vier und fünf"),
        ("Teil III", "Teil drei"),
        ("Band XII", "Band zwölf"),
        ("Abschnitt I", "Abschnitt eins"),
    ],
)
def test_roman_heading_german_labels(text: str, expected: str) -> None:
    assert german._normalize_roman_numerals(text) == expected


def test_roman_standalone_single_line() -> None:
    assert german._normalize_roman_numerals("VII.") == "sieben."


# --- Ordinals (heading context) ----------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Das 1. Kapitel beginnt hier.", "Das erste Kapitel beginnt hier."),
        ("Im 3. Buch steht es.", "Im dritte Buch steht es."),
        ("21. Auflage", "einundzwanzigste Auflage"),
    ],
)
def test_ordinals_before_heading(text: str, expected: str) -> None:
    assert german._normalize_ordinals(text) == expected


def test_digit_before_heading_stays_cardinal_without_period() -> None:
    assert german._normalize_ordinals("5 Kapitel") == "5 Kapitel"


# --- Full pipeline via normalize_german_lexical ------------------------------

def test_normalize_german_lexical_years() -> None:
    text = "Er wurde 1985 geboren und 2020 promoviert."
    expected = (
        "Er wurde neunzehnhundertfünfundachtzig geboren und zweitausendzwanzig promoviert."
    )
    assert german.normalize_german_lexical(text) == expected


def test_normalize_german_lexical_currency_and_number() -> None:
    text = "Die Miete beträgt €1.500 pro Monat."
    # A thousands-dot amount is read as a cardinal, not a year.
    result = german.normalize_german_lexical(text)
    assert "Euro" in result
    assert "1500" not in result
    assert "eintausendfünfhundert" in result


def test_normalize_german_lexical_abbreviations_and_roman() -> None:
    text = "Siehe Dr. Müller, Kapitel IV, z. B. Absatz 3."
    result = german.normalize_german_lexical(text)
    assert "Doktor Müller" in result
    assert "Kapitel vier" in result
    assert "zum Beispiel" in result


def test_normalize_german_lexical_era() -> None:
    text = "Caesar starb 44 v. Chr."
    result = german.normalize_german_lexical(text)
    assert "vierundvierzig" in result
    assert "vor Christus" in result


# --- Integration: prepare_tts_text with language="german" --------------------

def test_prepare_tts_text_german_dispatches_to_german_normalizer() -> None:
    text = "Das Jahr 1985 ist wichtig."
    result = prepare_tts_text(text, language="german")
    assert "neunzehnhundertfünfundachtzig" in result


def test_prepare_tts_text_german_leaves_abbrevs_dotted_if_unknown() -> None:
    # German abbreviates a number as "Nr.", not "No.", so the English form is
    # left untouched under the German profile.
    result = prepare_tts_text("She said No. 5.", language="german")
    assert "Nummer" not in result
    assert "number" not in result.lower()


def test_prepare_tts_text_german_currency() -> None:
    text = "Das kostet €50 pro Jahr."
    result = prepare_tts_text(text, language="german")
    assert "fünfzig Euro" in result
    assert "Euros" not in result


def test_prepare_tts_text_german_roman_heading() -> None:
    text = "Kapitel VII beginnt."
    result = prepare_tts_text(text, language="german")
    assert "Kapitel sieben" in result


def test_prepare_tts_text_german_era() -> None:
    text = "753 v. Chr. wurde Rom gegründet."
    result = prepare_tts_text(text, language="german")
    assert "vor Christus" in result
    assert "siebenhundertdreiundfünfzig" in result


def test_prepare_tts_text_default_language_is_english() -> None:
    result = prepare_tts_text("Chapter V")
    assert "five" in result.lower()
