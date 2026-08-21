"""English profile and the transforms unique to English.

Everything shared with the other languages lives in `engine`; this module
supplies the English vocabulary plus two things no other language needs:
spelling out URLs, and the pronoun-"I" guard that keeps "I said" from becoming
"one said".
"""
from __future__ import annotations

import re

from . import engine, numbers
from .profile import LanguageProfile

# ---------------------------------------------------------------------------
# URL spelling-out
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"(?:https?|ftp)://[^\s<>\"')\]]+", re.IGNORECASE)
_URL_SPELL_OUT = {"http", "https", "ftp", "www"}
_URL_PUNCT = {
    ":": "colon",
    "/": "slash",
    ".": "dot",
    "?": "question mark",
    "=": "equals",
    "&": "ampersand",
    "#": "hash",
    "_": "underscore",
    "-": "dash",
    "@": "at",
    "%": "percent",
    "~": "tilde",
}


def _url_to_spoken(match: re.Match[str]) -> str:
    url = match.group(0)
    trailing = ""
    while url and url[-1] in ".,;:!?":
        trailing = url[-1] + trailing
        url = url[:-1]
    parts: list[str] = []
    for token in re.findall(r"[a-zA-Z0-9]+|.", url):
        if token in _URL_PUNCT:
            parts.append(_URL_PUNCT[token])
        elif token.lower() in _URL_SPELL_OUT:
            parts.append("-".join(token.lower()))
        else:
            parts.append(token)
    return re.sub(r"\s+", " ", " ".join(parts)).strip() + trailing


def normalize_urls(text: str) -> str:
    if not text:
        return text
    return _URL_RE.sub(_url_to_spoken, text)


# ---------------------------------------------------------------------------
# Spoken-word shaping
# ---------------------------------------------------------------------------

_AND_RE = re.compile(r"\band\b")


def _tidy(spoken: str) -> str:
    """Drop the commas, hyphens, and "and" num2words writes into English."""
    spoken = spoken.replace(",", " ").replace("-", " ")
    return re.sub(r"\s+", " ", _AND_RE.sub(" ", spoken)).strip()


def _pluralize(word: str) -> str:
    if not word:
        return word
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return f"{word[:-1]}ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return f"{word}es"
    return f"{word}s"


def _pluralize_phrase(phrase: str) -> str:
    parts = phrase.split()
    if not parts:
        return phrase
    parts[-1] = _pluralize(parts[-1])
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

_ERA_LETTERS = ("BCE", "BC", "CE", "AD")
_ERA_DOTTED = (
    (r"\bB\s*\.\s*C\s*\.\s*E\s*\.?", "B-C-E"),
    (r"\bA\s*\.\s*D\s*\.?", "A-D"),
    (r"\bC\s*\.\s*E\s*\.?", "C-E"),
    (r"\bB\s*\.\s*C\s*\.(?!\s*E\s*\.?)", "B-C"),
)
# Plain era labels are matched case-sensitively — lowercase "ad" is the English
# word, and "3 ad hoc committees" must not become "three A-D hoc committees".
_ERA_YEAR = r"\d{1,4}(?:\s*[–-]\s*\d{1,4})?"
_ERA_PLAIN = tuple(
    rule
    for era in _ERA_LETTERS
    for rule in (
        (rf"(\b{_ERA_YEAR})\s+(?-i:{era})\b", rf"\1 {'-'.join(era)}"),
        (rf"\b(?-i:{era})\s+({_ERA_YEAR})\b", rf"{'-'.join(era)} \1"),
    )
)

PROFILE = LanguageProfile(
    name="english",
    n2w_lang="en",
    decimal_word="point",
    minus_word="minus",
    plus_word="plus",
    range_word="to",
    and_word="and",
    number_tidy=_tidy,
    thousands_sep=",",
    decimal_sep=".",
    pair_zero_word="oh",
    # English keeps no diacritics: the models read ASCII, and the Pali/Sanskrit
    # transliteration in `common` is written for exactly this case.
    native_letters=frozenset(),
    transliterate_indic=True,
    currency_units={
        "$": ("dollar", "dollars"),
        "€": ("euro", "euros"),
        "£": ("pound", "pounds"),
        "¥": ("yen", "yen"),
        "₹": ("rupee", "rupees"),
        "₽": ("ruble", "rubles"),
        "₩": ("won", "won"),
        "₪": ("shekel", "shekels"),
        "₫": ("dong", "dong"),
        "₴": ("hryvnia", "hryvnias"),
        "₦": ("naira", "naira"),
        "฿": ("baht", "baht"),
        "₺": ("lira", "lira"),
        "₱": ("peso", "pesos"),
    },
    scale_words={
        "hundred": ("hundred", "hundred"),
        "thousand": ("thousand", "thousand"),
        "million": ("million", "million"),
        "billion": ("billion", "billion"),
        "trillion": ("trillion", "trillion"),
        "quadrillion": ("quadrillion", "quadrillion"),
        "mn": ("million", "million"),
        "bn": ("billion", "billion"),
        "tn": ("trillion", "trillion"),
    },
    scale_abbrevs={
        "k": ("thousand", "thousand"),
        "m": ("million", "million"),
        "b": ("billion", "billion"),
        "t": ("trillion", "trillion"),
    },
    symbol_units={
        "%": ("percent", "percent"),
        "‰": ("per mille", "per mille"),
        "°": ("degree", "degrees"),
    },
    degree_scales={"C": "Celsius", "F": "Fahrenheit"},
    symbol_words={
        "+": "plus",
        "&": "and",
        "×": "times",
        "÷": "divided by",
        "=": "equals",
        "±": "plus or minus",
        "≈": "approximately",
        "≠": "not equal to",
        "≤": "less than or equal to",
        "≥": "greater than or equal to",
        "§": "section",
        "№": "number",
    },
    fraction_denominators={
        2: ("half", "halves"),
        3: ("third", "thirds"),
        4: ("quarter", "quarters"),
        5: ("fifth", "fifths"),
        6: ("sixth", "sixths"),
        8: ("eighth", "eighths"),
        10: ("tenth", "tenths"),
        16: ("sixteenth", "sixteenths"),
    },
    label_words=(
        "figure", "fig", "table", "chapter", "section", "part", "volume", "vol",
        "no", "appendix", "equation", "eq",
    ),
    roman_labels=(
        "chapter", "chapters", "book", "books", "part", "parts", "volume",
        "volumes", "vol", "vols", "section", "sections", "act", "acts",
        "scene", "scenes", "appendix", "appendixes", "appendices",
    ),
    roman_list_joiners=("and", "or"),
    guard_roman_i=True,
    roman_i_determiners=frozenset(
        {
            "a", "an", "another", "any", "each", "every", "his", "her", "its",
            "my", "no", "our", "some", "that", "the", "their", "this", "your",
        }
    ),
    unit_words=(
        "percent", "degrees", "degree", "metres", "meters", "kilometres",
        "kilometers", "kilograms", "grams", "miles", "feet", "inches",
        "acres", "seconds", "minutes", "hours", "words",
    ),
    abbrev_expansions={
        "prof": "professor",
        "fig": "figure",
        "figs": "figures",
        "approx": "approximately",
        "ca": "circa",
        "cf": "compare",
        "i.e": "that is",
        "e.g": "for example",
        "etc": "et cetera",
        "et al": "and others",
        "et seq": "and the following",
        "et seqq": "and the following",
        "ibid": "in the same place",
        "loc. cit": "in the place cited",
        "n.b": "note well",
        "op. cit": "in the work cited",
        "q.v": "which see",
        "vs": "versus",
        "viz": "namely",
    },
    numbered_abbrevs={
        "no": "number",
        "p": "page",
        "pp": "pages",
        "v": "verse",
        "vv": "verses",
    },
    dot_strip_abbrevs=("Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "St", "Fig", "Figs"),
    era_replacements=_ERA_DOTTED + _ERA_PLAIN,
    ordinal_patterns=(r"\b(?P<num>\d+)(?i:st|nd|rd|th)\b",),
    decade_pattern=r"(?<!\w)(?:['’])?(?P<num>\d{1,4})(?:['’])?s\b",
    decade_form=_pluralize_phrase,
    pre_hooks=(normalize_urls,),
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


def normalize_english_lexical(text: str) -> str:
    return engine.normalize_lexical(text, PROFILE)
