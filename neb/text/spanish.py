"""Spanish profile."""
from __future__ import annotations

import re

from . import engine, numbers
from .profile import LanguageProfile

_MASCULINE_ENDING_RE = re.compile(r"o\b")


def _feminine(ordinal: str) -> str:
    """"vigésimo primero" → "vigésima primera"."""
    return _MASCULINE_ENDING_RE.sub("a", ordinal)


PROFILE = LanguageProfile(
    name="spanish",
    n2w_lang="es",
    decimal_word="coma",
    minus_word="menos",
    plus_word="más",
    range_word="a",
    and_word="y",
    thousands_sep=".",
    decimal_sep=",",
    attributive_one="un",
    attributive_one_feminine="una",
    feminine_nouns=frozenset(
        {"libra", "rupia", "corona", "hora", "semana", "tonelada", "milla", "peseta"}
    ),
    native_letters=frozenset("áéíóúüñÁÉÍÓÚÜÑ"),
    currency_units={
        "$": ("dólar", "dólares"),
        "€": ("euro", "euros"),
        "£": ("libra", "libras"),
        "¥": ("yen", "yenes"),
        "₹": ("rupia", "rupias"),
        "₽": ("rublo", "rublos"),
        "₩": ("won", "wones"),
        "₪": ("séquel", "séqueles"),
        "฿": ("baht", "bahts"),
        "₺": ("lira", "liras"),
        "₱": ("peso", "pesos"),
    },
    scale_words={
        "mil": ("mil", "mil"),
        "millón": ("millón", "millones"),
        "millones": ("millón", "millones"),
        "mill": ("millón", "millones"),
        "billón": ("billón", "billones"),
        "billones": ("billón", "billones"),
    },
    scale_abbrevs={
        "k": ("mil", "mil"),
        "m": ("millón", "millones"),
    },
    scale_preposition="de",
    scale_preposition_exempt=frozenset({"mil"}),
    symbol_units={
        "%": ("por ciento", "por ciento"),
        "‰": ("por mil", "por mil"),
        "°": ("grado", "grados"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "más",
        "&": "y",
        "×": "por",
        "÷": "dividido por",
        "=": "igual",
        "±": "más menos",
        "≈": "aproximadamente",
        "§": "párrafo",
        "№": "número",
    },
    fraction_denominators={
        2: ("medio", "medios"),
        3: ("tercio", "tercios"),
        4: ("cuarto", "cuartos"),
        5: ("quinto", "quintos"),
        6: ("sexto", "sextos"),
        8: ("octavo", "octavos"),
        10: ("décimo", "décimos"),
    },
    label_words=(
        "figura", "fig", "tabla", "tab", "capítulo", "cap", "sección",
        "parte", "volumen", "vol", "número", "núm", "apéndice", "ecuación",
        "ec", "página", "pág",
    ),
    roman_labels=(
        "capítulo", "capítulos", "libro", "libros", "parte", "partes",
        "volumen", "volúmenes", "sección", "secciones", "acto", "actos",
        "escena", "escenas", "apéndice", "apéndices", "tomo", "tomos",
    ),
    roman_list_joiners=("y", "o", "e"),
    unit_words=(
        "céntimos", "centavos", "grados", "metros", "kilómetros", "kilogramos",
        "gramos", "litros", "segundos", "minutos", "horas", "días", "semanas",
        "meses", "años", "personas", "habitantes", "páginas", "palabras",
    ),
    multi_dot_abbrevs={
        "p. ej.": "por ejemplo",
        "p.ej.": "por ejemplo",
        "a. de C.": "antes de Cristo",
        "d. de C.": "después de Cristo",
    },
    abbrev_expansions={
        "sr": "señor",
        "sra": "señora",
        "srta": "señorita",
        "dr": "doctor",
        "dra": "doctora",
        "prof": "profesor",
        "etc": "etcétera",
        "aprox": "aproximadamente",
        "cfr": "confróntese",
        "ed": "edición",
        "trad": "traducción",
        "sig": "siguiente",
        "s": "siglo",
    },
    numbered_abbrevs={
        "n": "número",
        "núm": "número",
        "pág": "página",
        "págs": "páginas",
        "p": "página",
        "pp": "páginas",
        "cap": "capítulo",
        "vol": "volumen",
        "v": "versículo",
    },
    dot_strip_abbrevs=("Sr", "Sra", "Srta", "Dr", "Dra", "Prof", "Sto", "Sta"),
    era_replacements=(
        (r"\ba\s*\.\s*C\s*\.", "antes de Cristo"),
        (r"\bd\s*\.\s*C\s*\.", "después de Cristo"),
        (r"\ba\s*\.\s*e\s*\.\s*c\s*\.", "antes de la era común"),
    ),
    ordinal_patterns=(
        r"\b(?P<num>\d+)(?:(?P<fem>ª)|º|°)",
        r"\b(?P<num>\d+)(?:er|ro|do|to|mo|vo|no)\b",
    ),
    ordinal_feminine=_feminine,
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


def normalize_spanish_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
