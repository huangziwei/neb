"""Portuguese profile."""
from __future__ import annotations

import re

from . import engine, numbers
from .profile import LanguageProfile

_MASCULINE_ENDING_RE = re.compile(r"o\b")


def _feminine(ordinal: str) -> str:
    """"vigésimo primeiro" → "vigésima primeira"."""
    return _MASCULINE_ENDING_RE.sub("a", ordinal)


PROFILE = LanguageProfile(
    name="portuguese",
    n2w_lang="pt",
    decimal_word="vírgula",
    minus_word="menos",
    plus_word="mais",
    range_word="a",
    and_word="e",
    thousands_sep=".",
    decimal_sep=",",
    attributive_one="um",
    attributive_one_feminine="uma",
    feminine_nouns=frozenset(
        {"libra", "rupia", "coroa", "hora", "semana", "tonelada", "milha"}
    ),
    native_letters=frozenset("áâãàçéêíóôõúÁÂÃÀÇÉÊÍÓÔÕÚ"),
    currency_units={
        "$": ("dólar", "dólares"),
        "€": ("euro", "euros"),
        "£": ("libra", "libras"),
        "¥": ("iene", "ienes"),
        "₹": ("rupia", "rupias"),
        "₽": ("rublo", "rublos"),
        "₩": ("won", "wons"),
        "₪": ("shekel", "shekels"),
        "฿": ("baht", "bahts"),
        "₺": ("lira", "liras"),
        "₱": ("peso", "pesos"),
    },
    scale_words={
        "mil": ("mil", "mil"),
        "milhar": ("milhar", "milhares"),
        "milhares": ("milhar", "milhares"),
        "milhão": ("milhão", "milhões"),
        "milhões": ("milhão", "milhões"),
        "bilhão": ("bilhão", "bilhões"),
        "bilhões": ("bilhão", "bilhões"),
        "bilião": ("bilião", "biliões"),
        "biliões": ("bilião", "biliões"),
    },
    scale_abbrevs={
        "k": ("mil", "mil"),
        "m": ("milhão", "milhões"),
    },
    scale_preposition="de",
    scale_preposition_exempt=frozenset({"mil", "milhar", "milhares"}),
    symbol_units={
        "%": ("por cento", "por cento"),
        "‰": ("por mil", "por mil"),
        "°": ("grau", "graus"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "mais",
        "&": "e",
        "×": "vezes",
        "÷": "dividido por",
        "=": "igual",
        "±": "mais ou menos",
        "≈": "aproximadamente",
        "§": "parágrafo",
        "№": "número",
    },
    fraction_denominators={
        2: ("meio", "meios"),
        3: ("terço", "terços"),
        4: ("quarto", "quartos"),
        5: ("quinto", "quintos"),
        6: ("sexto", "sextos"),
        8: ("oitavo", "oitavos"),
        10: ("décimo", "décimos"),
    },
    label_words=(
        "figura", "fig", "tabela", "tab", "capítulo", "cap", "secção",
        "seção", "parte", "volume", "vol", "número", "apêndice", "equação",
        "eq", "página", "pág",
    ),
    roman_labels=(
        "capítulo", "capítulos", "livro", "livros", "parte", "partes",
        "volume", "volumes", "secção", "secções", "seção", "seções",
        "ato", "atos", "acto", "actos", "cena", "cenas",
        "apêndice", "apêndices", "tomo", "tomos",
    ),
    roman_list_joiners=("e", "ou"),
    unit_words=(
        "cêntimos", "centavos", "graus", "metros", "quilómetros", "quilômetros",
        "quilogramas", "gramas", "litros", "segundos", "minutos", "horas",
        "dias", "semanas", "meses", "anos", "pessoas", "habitantes",
        "páginas", "palavras",
    ),
    multi_dot_abbrevs={
        "p. ex.": "por exemplo",
        "p.ex.": "por exemplo",
    },
    abbrev_expansions={
        "sr": "senhor",
        "sra": "senhora",
        "dr": "doutor",
        "dra": "doutora",
        "prof": "professor",
        "etc": "etcétera",
        "aprox": "aproximadamente",
        "cfr": "confronte",
        "ed": "edição",
        "trad": "tradução",
        "séc": "século",
    },
    numbered_abbrevs={
        "n": "número",
        "pág": "página",
        "págs": "páginas",
        "p": "página",
        "pp": "páginas",
        "cap": "capítulo",
        "vol": "volume",
        "v": "versículo",
    },
    dot_strip_abbrevs=("Sr", "Sra", "Dr", "Dra", "Prof", "Sto", "Sta", "S"),
    era_replacements=(
        (r"\ba\s*\.\s*C\s*\.", "antes de Cristo"),
        (r"\bd\s*\.\s*C\s*\.", "depois de Cristo"),
    ),
    ordinal_patterns=(r"\b(?P<num>\d+)(?:(?P<fem>ª)|º|°)",),
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


def normalize_portuguese_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
