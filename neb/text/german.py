"""German profile.

German's departures from the shared pipeline are all data, not code.
"""
from __future__ import annotations

from . import engine, numbers
from .profile import LanguageProfile

_MONTHS = (
    "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
    "September", "Oktober", "November", "Dezember", "Jänner",
)

# Heading nouns that turn a bare "5." into an ordinal rather than a sentence end.
_ORDINAL_HEADINGS = (
    "Kapitel", "Kapitels", "Buch", "Buches", "Teil", "Teils", "Teiles",
    "Band", "Bandes", "Abschnitt", "Abschnitts", "Akt", "Aktes", "Szene",
    "Anhang", "Anhangs", "Auflage",
)


def _decade(spoken: str) -> str:
    return f"{spoken}er"


PROFILE = LanguageProfile(
    name="german",
    n2w_lang="de",
    decimal_word="Komma",
    minus_word="minus",
    plus_word="plus",
    range_word="bis",
    and_word="und",
    thousands_sep=".",
    decimal_sep=",",
    attributive_one="ein",
    attributive_one_feminine="eine",
    feminine_nouns=frozenset(
        {
            "Million", "Milliarde", "Billion", "Lira", "Rupie", "Krone",
            "Sekunde", "Minute", "Stunde", "Woche", "Meile", "Tonne",
        }
    ),
    native_letters=frozenset("äöüÄÖÜßẞ"),
    currency_units={
        "$": ("Dollar", "Dollar"),
        "€": ("Euro", "Euro"),
        "£": ("Pfund", "Pfund"),
        "¥": ("Yen", "Yen"),
        "₹": ("Rupie", "Rupien"),
        "₽": ("Rubel", "Rubel"),
        "₩": ("Won", "Won"),
        "₪": ("Schekel", "Schekel"),
        "฿": ("Baht", "Baht"),
        "₺": ("Lira", "Lira"),
        "₱": ("Peso", "Pesos"),
    },
    scale_words={
        "hundert": ("Hundert", "Hundert"),
        "tausend": ("Tausend", "Tausend"),
        "tsd": ("Tausend", "Tausend"),
        "million": ("Million", "Millionen"),
        "millionen": ("Million", "Millionen"),
        "mio": ("Million", "Millionen"),
        "milliarde": ("Milliarde", "Milliarden"),
        "milliarden": ("Milliarde", "Milliarden"),
        "mrd": ("Milliarde", "Milliarden"),
        "billion": ("Billion", "Billionen"),
        "billionen": ("Billion", "Billionen"),
        "bio": ("Billion", "Billionen"),
    },
    scale_abbrevs={
        "k": ("Tausend", "Tausend"),
        "m": ("Million", "Millionen"),
        "b": ("Milliarde", "Milliarden"),
        "t": ("Billion", "Billionen"),
    },
    symbol_units={
        "%": ("Prozent", "Prozent"),
        "‰": ("Promille", "Promille"),
        "°": ("Grad", "Grad"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "plus",
        "&": "und",
        "×": "mal",
        "÷": "geteilt durch",
        "=": "gleich",
        "±": "plus minus",
        "≈": "ungefähr",
        "§": "Paragraf",
        "№": "Nummer",
    },
    fraction_denominators={
        2: ("halb", "halbe"),
        3: ("Drittel", "Drittel"),
        4: ("Viertel", "Viertel"),
        5: ("Fünftel", "Fünftel"),
        6: ("Sechstel", "Sechstel"),
        8: ("Achtel", "Achtel"),
        10: ("Zehntel", "Zehntel"),
        16: ("Sechzehntel", "Sechzehntel"),
    },
    label_words=(
        "Abbildung", "Abb", "Tabelle", "Tab", "Kapitel", "Kap", "Teil", "Band",
        "Bd", "Abschnitt", "Nummer", "Nr", "Seite", "S", "Gleichung", "Gl",
    ),
    roman_labels=(
        "Kapitel", "Buch", "Bücher", "Teil", "Teile", "Band", "Bände",
        "Abschnitt", "Abschnitte", "Akt", "Akte", "Szene", "Szenen",
        "Anhang", "Anhänge",
    ),
    roman_list_joiners=("und", "oder"),
    unit_words=(
        "Cent", "Prozent", "Promille", "Grad", "Stück", "Meter", "Kilometer",
        "Zentimeter", "Millimeter", "Kilogramm", "Gramm", "Tonnen", "Liter",
        "Sekunden", "Sekunde", "Minuten", "Minute", "Stunden", "Stunde",
        "Tage", "Tag", "Wochen", "Monate", "Jahre", "Jahren", "Menschen",
        "Einwohner", "Seiten", "Wörter", "Kilometern", "Metern",
    ),
    multi_dot_abbrevs={
        "z. B.": "zum Beispiel",
        "z.B.": "zum Beispiel",
        "d. h.": "das heißt",
        "d.h.": "das heißt",
        "s. o.": "siehe oben",
        "s.o.": "siehe oben",
        "s. u.": "siehe unten",
        "s.u.": "siehe unten",
        "u. a.": "unter anderem",
        "u.a.": "unter anderem",
        "z. T.": "zum Teil",
        "z.T.": "zum Teil",
        "u. U.": "unter Umständen",
        "u.U.": "unter Umständen",
        "v. a.": "vor allem",
        "v.a.": "vor allem",
        "n. d.": "nach dem",
        "n.d.": "nach dem",
    },
    abbrev_expansions={
        "dr": "Doktor",
        "prof": "Professor",
        "hr": "Herr",
        "hrn": "Herrn",
        "fr": "Frau",
        "jh": "Jahrhundert",
        "jhdt": "Jahrhundert",
        "bzw": "beziehungsweise",
        "usw": "und so weiter",
        "etc": "et cetera",
        "ca": "circa",
        "ggf": "gegebenenfalls",
        "vgl": "vergleiche",
        "evtl": "eventuell",
        "sog": "sogenannt",
        "inkl": "inklusive",
        "exkl": "exklusive",
        "geb": "geboren",
        "gest": "gestorben",
        "geg": "gegeben",
        "st": "Sankt",
    },
    numbered_abbrevs={
        "nr": "Nummer",
        "s": "Seite",
        "abb": "Abbildung",
        "tab": "Tabelle",
        "kap": "Kapitel",
        "bd": "Band",
    },
    dot_strip_abbrevs=("Dr", "Prof", "Hr", "Hrn", "Fr", "St"),
    era_replacements=(
        (r"\bv\s*\.\s*u\s*\.\s*Z\s*\.?", "vor unserer Zeitrechnung"),
        (r"\bn\s*\.\s*u\s*\.\s*Z\s*\.?", "nach unserer Zeitrechnung"),
        (r"\bv\s*\.\s*Chr\s*\.?", "vor Christus"),
        (r"\bn\s*\.\s*Chr\s*\.?", "nach Christus"),
    ),
    ordinal_patterns=(
        r"\b(?P<num>\d{1,4})\.(?=\s+(?:" + "|".join(_ORDINAL_HEADINGS) + r")\b)",
    ),
    month_words=_MONTHS,
    month_dative_preps=frozenset({"am", "vom", "zum", "beim", "seit", "bis", "nach", "vor"}),
    decade_pattern=r"\b(?P<num>\d{1,4})er\b",
    decade_form=_decade,
)


# ---------------------------------------------------------------------------
# Shared transforms bound to this profile
# ---------------------------------------------------------------------------

def _int_to_words(value: int) -> str:
    return numbers.cardinal(value, PROFILE)


def _int_to_ordinal_words(value: int) -> str:
    return numbers.ordinal(value, PROFILE)


def _year_to_words(value: int) -> str:
    return numbers.year(value, PROFILE)


def _digits_to_words(token: str) -> str:
    return numbers.digit_string(token, PROFILE)


def _number_run_to_words(token: str) -> str:
    return numbers.number_token(token, PROFILE)


def _normalize_currency_symbols(text: str) -> str:
    return engine.normalize_currency(text, PROFILE)


def _normalize_era_abbreviations(text: str) -> str:
    return engine.normalize_eras(text, PROFILE)


def _normalize_roman_numerals(text: str) -> str:
    return engine.normalize_roman_numerals(text, PROFILE)


def _normalize_ordinals(text: str) -> str:
    return engine.normalize_ordinals(text, PROFILE)


def _roman_to_int(value: str):
    return engine.roman_to_int(value)


def normalize_abbreviations(text: str) -> str:
    return engine.normalize_abbreviations(text, PROFILE)


def normalize_numbers_for_tts(text: str) -> str:
    return engine.normalize_numbers(text, PROFILE)


def normalize_german_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
