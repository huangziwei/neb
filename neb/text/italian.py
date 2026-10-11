"""Italian profile."""
from __future__ import annotations

import re

from . import engine, numbers
from .profile import LanguageProfile

_MASCULINE_ENDING_RE = re.compile(r"o\b")


def _feminine(ordinal: str) -> str:
    """"ventunesimo" → "ventunesima"; every -o ending turns to -a."""
    return _MASCULINE_ENDING_RE.sub("a", ordinal)


PROFILE = LanguageProfile(
    name="italian",
    n2w_lang="it",
    decimal_word="virgola",
    minus_word="meno",
    plus_word="più",
    range_word="a",
    and_word="e",
    thousands_sep=".",
    decimal_sep=",",
    attributive_one="un",
    attributive_one_feminine="una",
    feminine_nouns=frozenset(
        {"sterlina", "lira", "rupia", "corona", "ora", "settimana", "tonnellata"}
    ),
    native_letters=frozenset("àèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ"),
    currency_units={
        "$": ("dollaro", "dollari"),
        "€": ("euro", "euro"),
        "£": ("sterlina", "sterline"),
        "¥": ("yen", "yen"),
        "₹": ("rupia", "rupie"),
        "₽": ("rublo", "rubli"),
        "₩": ("won", "won"),
        "₪": ("siclo", "sicli"),
        "฿": ("baht", "baht"),
        "₺": ("lira", "lire"),
        "₱": ("peso", "pesos"),
    },
    scale_words={
        "mila": ("mila", "mila"),
        "milione": ("milione", "milioni"),
        "milioni": ("milione", "milioni"),
        "mln": ("milione", "milioni"),
        "miliardo": ("miliardo", "miliardi"),
        "miliardi": ("miliardo", "miliardi"),
        "mld": ("miliardo", "miliardi"),
        "bilione": ("bilione", "bilioni"),
        "bilioni": ("bilione", "bilioni"),
    },
    scale_abbrevs={
        "k": ("mila", "mila"),
        "m": ("milione", "milioni"),
        "b": ("miliardo", "miliardi"),
        "t": ("bilione", "bilioni"),
    },
    scale_preposition="di",
    scale_preposition_exempt=frozenset({"mila"}),
    symbol_units={
        "%": ("per cento", "per cento"),
        "‰": ("per mille", "per mille"),
        "°": ("grado", "gradi"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "più",
        "&": "e",
        "×": "per",
        "÷": "diviso",
        "=": "uguale",
        "±": "più o meno",
        "≈": "circa",
        "§": "paragrafo",
        "№": "numero",
    },
    fraction_denominators={
        2: ("mezzo", "mezzi"),
        3: ("terzo", "terzi"),
        4: ("quarto", "quarti"),
        5: ("quinto", "quinti"),
        6: ("sesto", "sesti"),
        8: ("ottavo", "ottavi"),
        10: ("decimo", "decimi"),
        16: ("sedicesimo", "sedicesimi"),
    },
    label_words=(
        "figura", "fig", "tabella", "tab", "capitolo", "cap", "sezione",
        "parte", "volume", "vol", "numero", "appendice", "equazione", "eq",
        "pagina", "pag",
    ),
    roman_labels=(
        "capitolo", "capitoli", "libro", "libri", "parte", "parti", "volume",
        "volumi", "sezione", "sezioni", "atto", "atti", "scena", "scene",
        "appendice", "appendici", "tomo", "tomi",
    ),
    roman_list_joiners=("e", "o", "ed"),
    unit_words=(
        "centesimi", "gradi", "metri", "chilometri", "chilogrammi", "grammi",
        "litri", "secondi", "minuti", "ore", "giorni", "settimane", "mesi",
        "anni", "persone", "abitanti", "pagine", "parole",
    ),
    multi_dot_abbrevs={
        "p. es.": "per esempio",
        "p.es.": "per esempio",
        "ecc.": "eccetera",
        "sig.ra": "signora",
        "sig.na": "signorina",
    },
    abbrev_expansions={
        "dott": "dottor",
        "prof": "professor",
        "sig": "signor",
        "avv": "avvocato",
        "ing": "ingegner",
        "arch": "architetto",
        "cfr": "confronta",
        "ca": "circa",
        "ecc": "eccetera",
        "vedi": "vedi",
        "sec": "secolo",
    },
    numbered_abbrevs={
        "n": "numero",
        "nn": "numeri",
        "pag": "pagina",
        "pagg": "pagine",
        "p": "pagina",
        "pp": "pagine",
        "v": "versetto",
        "vv": "versetti",
        "cap": "capitolo",
        "vol": "volume",
    },
    dot_strip_abbrevs=("Sig", "Dott", "Prof", "Ing", "Avv", "Arch", "S"),
    era_replacements=(
        (r"\ba\s*\.\s*C\s*\.", "avanti Cristo"),
        (r"\bd\s*\.\s*C\s*\.", "dopo Cristo"),
        (r"\ba\s*\.\s*e\s*\.\s*v\s*\.", "avanti era volgare"),
        (r"\be\s*\.\s*v\s*\.", "era volgare"),
    ),
    ordinal_patterns=(r"\b(?P<num>\d+)(?:(?P<fem>ª)|º|°)",),
    ordinal_feminine=_feminine,
)


# --- Shared transforms bound to this profile ---------------------------------

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


def normalize_italian_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
