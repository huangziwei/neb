"""French profile.

A pre-hook folds typographic spaces so the amount pattern sees plain ones.
"""
from __future__ import annotations

import re

from . import engine, numbers
from .profile import LanguageProfile

# Only a space sitting between a digit and an exact three-digit group is part of
# a number; every other space is left alone.
_DIGIT_GROUP_SPACE_RE = re.compile(r"(?<=\d)[   ](?=\d{3}\b)")


def _normalize_digit_spaces(text: str) -> str:
    return _DIGIT_GROUP_SPACE_RE.sub(" ", text)


# "M." is Monsieur before a name, but a bare initial inside a run of them
# ("J. M. Dupont"), which the shared initialism rule handles instead.
_MONSIEUR_RE = re.compile(r"(?<!\w\.)(?<!\w\.\s)\bM\.(?=\s+[A-ZÀ-Ý])")


def _expand_monsieur(text: str) -> str:
    return _MONSIEUR_RE.sub("Monsieur", text)


def _feminine(ordinal: str) -> str:
    """Only "premier" inflects; the -ième ordinals are already epicene."""
    return re.sub(r"\bpremier\b", "première", ordinal)


PROFILE = LanguageProfile(
    name="french",
    n2w_lang="fr",
    decimal_word="virgule",
    minus_word="moins",
    plus_word="plus",
    range_word="à",
    and_word="et",
    thousands_sep=" ",
    decimal_sep=",",
    attributive_one="un",
    attributive_one_feminine="une",
    feminine_nouns=frozenset(
        {"livre", "roupie", "couronne", "heure", "semaine", "tonne", "minute", "seconde"}
    ),
    native_letters=frozenset("àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ"),
    currency_units={
        "$": ("dollar", "dollars"),
        "€": ("euro", "euros"),
        "£": ("livre", "livres"),
        "¥": ("yen", "yens"),
        "₹": ("roupie", "roupies"),
        "₽": ("rouble", "roubles"),
        "₩": ("won", "wons"),
        "₪": ("shekel", "shekels"),
        "฿": ("baht", "bahts"),
        "₺": ("lire", "lires"),
        "₱": ("peso", "pesos"),
    },
    scale_words={
        "mille": ("mille", "mille"),
        "million": ("million", "millions"),
        "millions": ("million", "millions"),
        "milliard": ("milliard", "milliards"),
        "milliards": ("milliard", "milliards"),
        "billion": ("billion", "billions"),
        "billions": ("billion", "billions"),
    },
    scale_abbrevs={
        "k": ("mille", "mille"),
        "m": ("million", "millions"),
        "b": ("milliard", "milliards"),
        "t": ("billion", "billions"),
    },
    scale_preposition="de",
    scale_preposition_exempt=frozenset({"mille"}),
    symbol_units={
        "%": ("pour cent", "pour cent"),
        "‰": ("pour mille", "pour mille"),
        "°": ("degré", "degrés"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "plus",
        "&": "et",
        "×": "fois",
        "÷": "divisé par",
        "=": "égale",
        "±": "plus ou moins",
        "≈": "environ",
        "§": "paragraphe",
        "№": "numéro",
    },
    fraction_denominators={
        2: ("demi", "demis"),
        3: ("tiers", "tiers"),
        4: ("quart", "quarts"),
        5: ("cinquième", "cinquièmes"),
        6: ("sixième", "sixièmes"),
        8: ("huitième", "huitièmes"),
        10: ("dixième", "dixièmes"),
        16: ("seizième", "seizièmes"),
    },
    label_words=(
        "figure", "fig", "tableau", "tab", "chapitre", "chap", "section",
        "partie", "volume", "vol", "numéro", "annexe", "équation", "éq",
        "page", "p",
    ),
    roman_labels=(
        "chapitre", "chapitres", "livre", "livres", "partie", "parties",
        "volume", "volumes", "section", "sections", "acte", "actes",
        "scène", "scènes", "annexe", "annexes", "tome", "tomes",
    ),
    roman_list_joiners=("et", "ou"),
    unit_words=(
        "centimes", "degrés", "mètres", "kilomètres", "kilogrammes", "grammes",
        "litres", "secondes", "minutes", "heures", "jours", "semaines", "mois",
        "ans", "années", "personnes", "habitants", "pages", "mots",
    ),
    multi_dot_abbrevs={
        "c.-à-d.": "c'est-à-dire",
        "p. ex.": "par exemple",
        "p.ex.": "par exemple",
    },
    abbrev_expansions={
        "mme": "Madame",
        "mlle": "Mademoiselle",
        "dr": "Docteur",
        "pr": "Professeur",
        "etc": "et cetera",
        "cf": "confer",
        "env": "environ",
        "av": "avant",
        "ap": "après",
        "éd": "édition",
        "trad": "traduction",
    },
    numbered_abbrevs={
        "no": "numéro",
        "nos": "numéros",
        "p": "page",
        "pp": "pages",
        "chap": "chapitre",
        "vol": "volume",
        "fig": "figure",
        "v": "verset",
    },
    dot_strip_abbrevs=("M", "MM", "Mme", "Mlle", "Dr", "Pr", "St", "Ste"),
    era_replacements=(
        (r"\bav\s*\.\s*J\s*\.?\s*-?\s*C\s*\.?", "avant Jésus-Christ"),
        (r"\bap\s*\.\s*J\s*\.?\s*-?\s*C\s*\.?", "après Jésus-Christ"),
        (r"\bJ\s*\.\s*-?\s*C\s*\.", "Jésus-Christ"),
    ),
    ordinal_patterns=(
        r"\b(?P<num>\d+)(?:(?P<fem>re|ère|nde)|er|ème|ième|nd|e)\b",
    ),
    ordinal_feminine=_feminine,
    pre_hooks=(_normalize_digit_spaces, _expand_monsieur),
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


def normalize_french_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
