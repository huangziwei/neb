"""The language-agnostic normalization pipeline.

Every lexical transform lives here once and reads its vocabulary from a
`LanguageProfile`. The regexes each profile implies are compiled once and
cached, so a chapter pays the build cost a single time.

Pipeline order matters and is fixed by `normalize_lexical`:

  1. profile pre-hooks        — e.g. English URL spelling-out, before dots move
  2. abbreviations            — expand or de-dot, so the chunker sees no false
                                sentence ends
  3. era markers              — "B.C." before dotted initialisms claim it
  4. Roman numerals           — while headings still carry their labels
  5. currency and quantities  — consume digits that carry a noun, so a price
                                like "1500 Euro" never reaches the year rule
  6. symbols, fractions, times
  7. numbers                  — everything still written in digits
  8. profile post-hooks
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from re import Pattern

from . import numbers
from .profile import LanguageProfile, SpokenNoun

# Punctuation that may trail a heading numeral. Mirrors the sets in common.py;
# kept local so the Roman-numeral trail test stays a concern of this module.
_HEADING_TRAIL_PUNCT = (
    {".", "!", "?"} | {",", ";", ":"} | set("\"')]}" + "”’") | {"-", "–", "—"}
)

_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
_ROMAN_CANONICAL_RE = re.compile(
    r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
)
_ROMAN_TOKEN_RE = re.compile(r"\b[IVXLCDM]+\b", re.IGNORECASE)
_RESIDUAL_DIGITS_RE = re.compile(r"\d+")
_LETTER = r"[^\W\d_]"


def roman_to_int(value: str) -> int | None:
    """Value of a canonical Roman numeral, or None if it is not one."""
    roman = value.upper()
    if not roman or not _ROMAN_CANONICAL_RE.fullmatch(roman):
        return None
    total = 0
    prev = 0
    for ch in reversed(roman):
        number = _ROMAN_VALUES.get(ch)
        if number is None:
            return None
        if number < prev:
            total -= number
        else:
            total += number
            prev = number
    return total or None


def _match_case(expansion: str, source: str) -> str:
    """Re-case an expansion to match the abbreviation it replaces."""
    if source.isupper() and len(source) > 1:
        return expansion.upper()
    if source[:1].isupper():
        return expansion[:1].upper() + expansion[1:]
    return expansion


def _alternation(words: Sequence[str]) -> str:
    """Regex alternation, longest first so prefixes cannot win early."""
    ordered = sorted({w for w in words if w}, key=len, reverse=True)
    return "|".join(re.escape(w) for w in ordered)


# ---------------------------------------------------------------------------
# Compiled per-profile rules
# ---------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class _Rules:
    amount: str
    currency_prefix: Pattern[str] | None
    currency_suffix: Pattern[str] | None
    quantity: Pattern[str] | None
    bare_scale: Pattern[str] | None
    noun_lookup: dict[str, SpokenNoun]
    scale_lookup: dict[str, SpokenNoun]
    symbol_unit: Pattern[str] | None
    degree_scale: Pattern[str] | None
    symbol_word: Pattern[str] | None
    ascii_fraction: Pattern[str] | None
    unicode_fraction: Pattern[str] | None
    mixed_fraction: Pattern[str] | None
    clock: Pattern[str]
    label_number: Pattern[str] | None
    grouped_int: Pattern[str]
    decimal: Pattern[str]
    dotted_run: Pattern[str]
    signed_int: Pattern[str]
    decade: Pattern[str] | None
    year_range: Pattern[str]
    year: Pattern[str]
    ordinals: tuple[Pattern[str], ...]
    month_ordinal: Pattern[str] | None
    multi_dot: tuple[tuple[str, str], ...]
    abbrev: Pattern[str] | None
    numbered_abbrev: Pattern[str] | None
    dot_strip: Pattern[str] | None
    era: tuple[tuple[Pattern[str], str], ...]
    roman_heading: Pattern[str] | None
    roman_leading_title: Pattern[str]
    roman_colon_heading: Pattern[str]
    roman_standalone: Pattern[str]
    roman_decimal: Pattern[str]


@cache
def _rules(profile: LanguageProfile) -> _Rules:
    ts = re.escape(profile.thousands_sep)
    ds = re.escape(profile.decimal_sep)
    # Thousands groups must be exactly three digits, so a decimal comma is never
    # mistaken for a group and the amount never ends on the separator itself.
    grouped = rf"\d{{1,3}}(?:{ts}\d{{3}})+|\d+"
    amount = rf"[+-]?(?:(?:{grouped})(?:{ds}\d+)?|{ds}\d+)"

    # Spelled-out and unambiguous abbreviations are safe anywhere; single-letter
    # ones are not ("20 m" is metres, "$20m" is millions), so they join only the
    # currency patterns.
    scale_plain = {k.lower(): v for k, v in profile.scale_words.items()}
    scale_lookup = dict(scale_plain)
    scale_lookup.update({k.lower(): v for k, v in profile.scale_abbrevs.items()})

    def _scale_group(table: dict[str, SpokenNoun]) -> str:
        # A scale token may be glued to the amount ("$1bn") or spaced
        # ("$1 billion"), but must not head a longer word ("$3 more").
        if not table:
            return ""
        return rf"(?:\s*(?P<scale>{_alternation(list(table))})\.?(?!{_LETTER}))?"

    scale_group = _scale_group(scale_lookup)
    plain_scale_group = _scale_group(scale_plain)

    noun_lookup: dict[str, SpokenNoun] = {}
    for unit in profile.currency_units.values():
        for form in unit:
            noun_lookup[form.lower()] = unit
    for word in profile.unit_words:
        noun_lookup.setdefault(word.lower(), (word, word))

    # Scale and noun tables are keyed lowercase, so every pattern that consults
    # them matches case-insensitively — "Mrd." and "Euro" must find "mrd" and
    # "euro".
    symbols = "".join(re.escape(s) for s in profile.currency_units)
    currency_prefix = currency_suffix = None
    if symbols:
        currency_prefix = re.compile(
            rf"(?<!\w)(?P<sym>[{symbols}])\s*(?P<amount>{amount}){scale_group}",
            re.IGNORECASE,
        )
        currency_suffix = re.compile(
            rf"(?P<amount>{amount}){scale_group}\s*(?P<sym>[{symbols}])(?!\w)",
            re.IGNORECASE,
        )

    quantity = None
    if noun_lookup:
        nouns = _alternation(list(noun_lookup))
        quantity = re.compile(
            rf"(?<!\w)(?P<amount>{amount}){plain_scale_group}\s+(?P<noun>{nouns})"
            rf"(?!{_LETTER})",
            re.IGNORECASE,
        )

    bare_scale = None
    if scale_plain:
        bare_scale = re.compile(
            rf"(?<!\w)(?P<amount>{amount})\s*(?P<scale>{_alternation(list(scale_plain))})"
            rf"\.?(?!{_LETTER})",
            re.IGNORECASE,
        )

    symbol_unit = degree_scale = None
    if profile.symbol_units:
        unit_syms = "".join(re.escape(s) for s in profile.symbol_units)
        symbol_unit = re.compile(rf"(?P<amount>{amount})\s*(?P<sym>[{unit_syms}])")
        if "°" in profile.symbol_units:
            degree_scale = re.compile(r"°\s*(?P<scale>[CF])(?![^\W\d_])")

    symbol_word = None
    if profile.symbol_words:
        symbol_word = re.compile(
            rf"(?<=\s)(?P<sym>{_alternation(list(profile.symbol_words))})(?=\s)"
        )

    ascii_fraction = unicode_fraction = mixed_fraction = None
    if profile.fraction_denominators:
        # Reject anything touching another digit or slash, so dates like
        # "3/4/2020" and ratios like "16/9/4" are left alone.
        ascii_fraction = re.compile(
            r"(?<![\d/])(?P<num>\d{1,2})\s*/\s*(?P<den>\d{1,2})(?![\d/])"
        )
        unicode_fraction = re.compile(r"[¼-¾⅐-⅞]")
        # "1½ cups" is a mixed number, not the digit 1 beside a fraction.
        mixed_fraction = re.compile(r"(?P<whole>\d+)\s*(?P<frac>[¼-¾⅐-⅞])")

    label_number = None
    if profile.label_words:
        label_number = re.compile(
            rf"\b(?P<label>{_alternation(profile.label_words)})\.?"
            r"\s+(?P<num>\d+(?:\.\d+)+)\b",
            re.IGNORECASE,
        )

    decade = (
        re.compile(profile.decade_pattern) if profile.decade_pattern else None
    )

    joiners = _alternation(profile.roman_list_joiners)
    roman_heading = None
    if profile.roman_labels:
        roman_heading = re.compile(
            rf"\b(?P<label>(?:{_alternation(profile.roman_labels)})\.?)"
            rf"\s+(?P<num>[IVXLCDM]+"
            rf"(?:\s*(?:,\s*(?:{joiners})\s+|,\s*|\s+(?:{joiners}|&)\s+)[IVXLCDM]+)*)\b",
            re.IGNORECASE,
        )

    numbered_abbrev = None
    if profile.numbered_abbrevs:
        # A digit may follow immediately ("Nr.5"), but a Roman numeral needs a
        # space — otherwise the M in "5 p.m." reads as the numeral 1000 and
        # turns the abbreviation into "pagem".
        numbered_abbrev = re.compile(
            rf"\b(?P<token>{_alternation(list(profile.numbered_abbrevs))})\."
            r"(?=\s*\d|\s+[IVXLCDM]+\b)",
            re.IGNORECASE,
        )

    return _Rules(
        amount=amount,
        currency_prefix=currency_prefix,
        currency_suffix=currency_suffix,
        quantity=quantity,
        bare_scale=bare_scale,
        noun_lookup=noun_lookup,
        scale_lookup=scale_lookup,
        symbol_unit=symbol_unit,
        degree_scale=degree_scale,
        symbol_word=symbol_word,
        ascii_fraction=ascii_fraction,
        unicode_fraction=unicode_fraction,
        mixed_fraction=mixed_fraction,
        clock=re.compile(r"(?<!\d)(?P<h>\d{1,2}):(?P<m>\d{2})(?::(?P<s>\d{2}))?(?!\d)"),
        label_number=label_number,
        grouped_int=re.compile(rf"\b\d{{1,3}}(?:{ts}\d{{3}})+\b"),
        decimal=re.compile(rf"\b\d+(?:{ds}\d+)+\b"),
        dotted_run=re.compile(r"\b\d+(?:\.\d+)+\b"),
        signed_int=re.compile(r"(?<!\w)(?P<sign>[+-])(?P<num>\d+)\b"),
        decade=decade,
        year_range=re.compile(
            r"\b(?P<start>1\d{3}|20\d{2})\s*[–-]\s*(?P<end>\d{2,4})\b(?!\s*[–-]\s*\d)"
        ),
        year=re.compile(r"\b(?P<year>1\d{3}|20\d{2})\b"),
        ordinals=tuple(re.compile(p) for p in profile.ordinal_patterns),
        month_ordinal=(
            re.compile(
                rf"\b(?P<num>\d{{1,2}})\.\s+(?P<month>{_alternation(profile.month_words)})\b"
            )
            if profile.month_words
            else None
        ),
        multi_dot=tuple(
            sorted(profile.multi_dot_abbrevs.items(), key=lambda kv: len(kv[0]), reverse=True)
        ),
        abbrev=(
            re.compile(
                rf"\b(?P<token>{_alternation(list(profile.abbrev_expansions))})\.",
                re.IGNORECASE,
            )
            if profile.abbrev_expansions
            else None
        ),
        numbered_abbrev=numbered_abbrev,
        dot_strip=(
            re.compile(
                rf"\b(?P<token>{_alternation(profile.dot_strip_abbrevs)})\.",
                re.IGNORECASE,
            )
            if profile.dot_strip_abbrevs
            else None
        ),
        era=tuple(
            (re.compile(pattern, re.IGNORECASE), repl)
            for pattern, repl in profile.era_replacements
        ),
        roman_heading=roman_heading,
        roman_leading_title=re.compile(
            r"^(?P<indent>[ \t]*)(?P<num>[IVXLCDM]+)(?P<trail>[^\w\n]*)[ \t]*\n"
            rf"(?=[ \t]*(?:{_LETTER}))",
            re.IGNORECASE,
        ),
        roman_colon_heading=re.compile(
            r"^(?P<indent>[ \t]*)(?P<num>[IVXLCDM]+)(?P<sep>\s*:\s*)",
            re.IGNORECASE | re.MULTILINE,
        ),
        roman_standalone=re.compile(
            r"^(?P<num>[IVXLCDM]+)(?P<trail>[^A-Za-z0-9]*)$", re.IGNORECASE
        ),
        roman_decimal=re.compile(r"\b(?P<roman>[IVXLCDM]+)\.(?P<num>\d+(?:\.\d+)*)\b"),
    )


# ---------------------------------------------------------------------------
# Amounts
# ---------------------------------------------------------------------------


def _amount_parts(amount: str, profile: LanguageProfile) -> tuple[str, str, str]:
    """Split a written amount into (sign, integer digits, fraction digits)."""
    value = amount
    sign = ""
    if value.startswith(("+", "-")):
        sign, value = value[0], value[1:]
    value = value.replace(profile.thousands_sep, "")
    if profile.decimal_sep in value:
        int_part, frac = value.split(profile.decimal_sep, 1)
    else:
        int_part, frac = value, ""
    if frac and all(ch == "0" for ch in frac):
        frac = ""
    return sign, int_part or "0", frac


def _is_one(int_part: str, frac: str) -> bool:
    return not frac and int_part.lstrip("0") == "1"


def _amount_to_words(amount: str, profile: LanguageProfile) -> str:
    sign, int_part, frac = _amount_parts(amount, profile)
    if frac:
        spoken = numbers.decimal(int_part, frac, profile)
    else:
        spoken = numbers.number_token(int_part, profile)
    if sign == "-":
        return f"{profile.minus_word} {spoken}"
    if sign == "+":
        return f"{profile.plus_word} {spoken}"
    return spoken


def _spoken_quantity(
    amount: str,
    scale_token: str | None,
    noun: SpokenNoun | None,
    profile: LanguageProfile,
    rules: _Rules,
) -> str:
    """Render "<amount> [scale] [noun]" with the right number and noun forms.

    A magnitude word always pluralizes the noun that follows it — "$1 billion"
    is "one billion dollars", never "one billion dollar".
    """
    _, int_part, frac = _amount_parts(amount, profile)
    singular = _is_one(int_part, frac)
    spoken = _amount_to_words(amount, profile)
    parts = [spoken]

    if scale_token:
        scale = rules.scale_lookup.get(scale_token.lower().rstrip("."))
        if scale:
            scale_word = scale[0] if singular else scale[1]
            parts[0] = numbers.attributive(spoken, scale_word, profile)
            parts.append(scale_word)
            singular = False

    if noun:
        noun_word = noun[0] if singular else noun[1]
        if len(parts) == 1:
            parts[0] = numbers.attributive(spoken, noun_word, profile)
        elif (
            profile.scale_preposition
            and parts[-1] not in profile.scale_preposition_exempt
        ):
            parts.append(profile.scale_preposition)
        parts.append(noun_word)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Abbreviations
# ---------------------------------------------------------------------------

_INITIALS_WITH_NAME_RE = re.compile(
    r"\b(?P<seq>[A-Z]\.(?:\s+[A-Z]\.)+)\s+(?P<name>[A-Z][^\W\d_'’\-]*[^\W\d_])\b"
)
_SPACED_DOTTED_INITIALISM_RE = re.compile(r"\b(?P<seq>[A-Z]\.(?:\s+[A-Z]\.)+)")
_COMPACT_DOTTED_INITIALISM_RE = re.compile(r"\b(?P<seq>(?:[A-Z][a-z]?\.){2,})")


def _hyphenate_dotted_letters(seq: str) -> str:
    segments = re.findall(r"[A-Za-z]+(?=\.)", seq)
    letters = [ch.upper() for seg in segments for ch in seg]
    if len(letters) < 2:
        return seq
    return "-".join(letters)


def _normalize_initialisms(text: str) -> str:
    def with_name(match: re.Match[str]) -> str:
        hyphenated = _hyphenate_dotted_letters(match.group("seq"))
        if hyphenated == match.group("seq"):
            return match.group(0)
        return f"{hyphenated}-{match.group('name')}"

    def bare(match: re.Match[str]) -> str:
        return _hyphenate_dotted_letters(match.group("seq"))

    text = _INITIALS_WITH_NAME_RE.sub(with_name, text)
    text = _SPACED_DOTTED_INITIALISM_RE.sub(bare, text)
    return _COMPACT_DOTTED_INITIALISM_RE.sub(bare, text)


def normalize_abbreviations(text: str, profile: LanguageProfile) -> str:
    if not text:
        return text
    rules = _rules(profile)

    for abbrev, expansion in rules.multi_dot:
        text = text.replace(abbrev, expansion)

    if rules.numbered_abbrev is not None:

        def numbered(match: re.Match[str]) -> str:
            # Spoken verbatim: each language writes the casing it wants, since
            # German capitalizes its nouns and English does not.
            expansion = profile.numbered_abbrevs.get(match.group("token").lower())
            return expansion or match.group(0)

        text = rules.numbered_abbrev.sub(numbered, text)

    if rules.abbrev is not None:

        def expand(match: re.Match[str]) -> str:
            token = match.group("token")
            expansion = profile.abbrev_expansions.get(token.lower())
            return _match_case(expansion, token) if expansion else match.group(0)

        text = rules.abbrev.sub(expand, text)

    text = _normalize_initialisms(text)

    if rules.dot_strip is not None:
        text = rules.dot_strip.sub(lambda m: m.group("token"), text)
    return text


def normalize_eras(text: str, profile: LanguageProfile) -> str:
    if not text:
        return text
    for pattern, replacement in _rules(profile).era:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Roman numerals
# ---------------------------------------------------------------------------


def normalize_roman_numerals(text: str, profile: LanguageProfile) -> str:
    rules = _rules(profile)

    def prev_word(start: int) -> str | None:
        match = re.search(rf"({_LETTER}+)\s*$", text[:start])
        return match.group(1) if match else None

    def next_word(start: int) -> str | None:
        match = re.search(rf"\b({_LETTER}+)", text[start:])
        return match.group(1) if match else None

    def next_non_space(start: int) -> str:
        match = re.search(r"\S", text[start:])
        return match.group(0) if match else ""

    def should_convert_bare_i(match: re.Match[str]) -> bool:
        """Guard the English pronoun "I" from becoming "one"."""
        label = match.group("label")
        if label and label[0].isupper():
            return True
        prev = prev_word(match.start())
        if prev and prev.lower() in profile.roman_i_determiners:
            return False
        next_char = next_non_space(match.end())
        if not next_char or next_char in _HEADING_TRAIL_PUNCT:
            return True
        token = next_word(match.end())
        return bool(token and token[0].isupper())

    def replace_heading(match: re.Match[str]) -> str:
        numbers_text = match.group("num")
        romans = list(_ROMAN_TOKEN_RE.finditer(numbers_text))
        if not romans:
            return match.group(0)
        if len(romans) == 1:
            roman = romans[0].group(0)
            value = roman_to_int(roman)
            if value is None:
                return match.group(0)
            if (
                profile.guard_roman_i
                and roman.upper() == "I"
                and not should_convert_bare_i(match)
            ):
                return match.group(0)
            return f"{match.group('label')} {numbers.cardinal(value, profile)}"

        parts: list[str] = []
        cursor = 0
        for roman_match in romans:
            start, end = roman_match.span()
            value = roman_to_int(roman_match.group(0))
            if value is None:
                return match.group(0)
            parts.append(numbers_text[cursor:start])
            parts.append(numbers.cardinal(value, profile))
            cursor = end
        parts.append(numbers_text[cursor:])
        return f"{match.group('label')} {''.join(parts)}"

    def replace_leading_title(match: re.Match[str]) -> str:
        value = roman_to_int(match.group("num"))
        if value is None:
            return match.group(0)
        trail = match.group("trail") or ""
        return f"{match.group('indent')}{numbers.cardinal(value, profile)}{trail}\n"

    def replace_colon_heading(match: re.Match[str]) -> str:
        value = roman_to_int(match.group("num"))
        if value is None:
            return match.group(0)
        return (
            f"{match.group('indent')}{numbers.cardinal(value, profile)}"
            f"{match.group('sep')}"
        )

    text = rules.roman_leading_title.sub(replace_leading_title, text, count=1)
    text = rules.roman_colon_heading.sub(replace_colon_heading, text)
    if rules.roman_heading is not None:
        text = rules.roman_heading.sub(replace_heading, text)

    match = rules.roman_standalone.fullmatch(text.strip())
    if not match:
        return text
    value = roman_to_int(match.group("num"))
    if value is None:
        return text
    return f"{numbers.cardinal(value, profile)}{match.group('trail') or ''}"


# ---------------------------------------------------------------------------
# Currency, quantities, symbols
# ---------------------------------------------------------------------------


def normalize_currency(text: str, profile: LanguageProfile) -> str:
    """Speak "$1 billion" as "one billion dollars", not "one dollar billion"."""
    if not text:
        return text
    rules = _rules(profile)
    if rules.currency_prefix is None or rules.currency_suffix is None:
        return text

    def replace(match: re.Match[str]) -> str:
        unit = profile.currency_units.get(match.group("sym"))
        if not unit:
            return match.group(0)
        scale = match.groupdict().get("scale")
        return _spoken_quantity(match.group("amount"), scale, unit, profile, rules)

    text = rules.currency_prefix.sub(replace, text)
    return rules.currency_suffix.sub(replace, text)


def normalize_quantities(text: str, profile: LanguageProfile) -> str:
    """Convert "1500 Euro" / "3 Millionen Menschen" while the noun is visible.

    Running before the year rule is what keeps a price from being read as a
    date: by the time years are considered, these digits are already words.
    """
    if not text:
        return text
    rules = _rules(profile)

    def replace(match: re.Match[str]) -> str:
        noun = rules.noun_lookup.get(match.group("noun").lower())
        if not noun:
            return match.group(0)
        scale = match.groupdict().get("scale")
        return _spoken_quantity(match.group("amount"), scale, noun, profile, rules)

    if rules.quantity is not None:
        text = rules.quantity.sub(replace, text)
    if rules.bare_scale is not None:
        # "5 Mio." on its own still needs its magnitude spoken.
        text = rules.bare_scale.sub(
            lambda m: _spoken_quantity(
                m.group("amount"), m.group("scale"), None, profile, rules
            ),
            text,
        )
    return text


def normalize_symbols(text: str, profile: LanguageProfile) -> str:
    if not text:
        return text
    rules = _rules(profile)

    if rules.degree_scale is not None:
        text = rules.degree_scale.sub(
            lambda m: "° " + profile.degree_scales.get(m.group("scale"), m.group("scale")),
            text,
        )

    if rules.symbol_unit is not None:

        def unit(match: re.Match[str]) -> str:
            noun = profile.symbol_units.get(match.group("sym"))
            if not noun:
                return match.group(0)
            return _spoken_quantity(match.group("amount"), None, noun, profile, rules)

        text = rules.symbol_unit.sub(unit, text)

    if rules.symbol_word is not None:
        text = rules.symbol_word.sub(
            lambda m: profile.symbol_words.get(m.group("sym"), m.group("sym")), text
        )
    return text


_UNICODE_FRACTIONS = {
    "¼": (1, 4), "½": (1, 2), "¾": (3, 4),
    "⅐": (1, 7), "⅑": (1, 9), "⅒": (1, 10),
    "⅓": (1, 3), "⅔": (2, 3), "⅕": (1, 5), "⅖": (2, 5), "⅗": (3, 5), "⅘": (4, 5),
    "⅙": (1, 6), "⅚": (5, 6), "⅛": (1, 8), "⅜": (3, 8), "⅝": (5, 8), "⅞": (7, 8),
}


def normalize_fractions(text: str, profile: LanguageProfile) -> str:
    if not text:
        return text
    rules = _rules(profile)
    if rules.unicode_fraction is None or rules.ascii_fraction is None:
        return text
    assert rules.mixed_fraction is not None

    def spoken(num: int, den: int) -> str | None:
        # A proper fraction only. "24/7" and "9/11" are idioms, not quantities.
        if num >= den:
            return None
        denominator = profile.fraction_denominators.get(den)
        if denominator is None:
            return None
        word = denominator[0] if num == 1 else denominator[1]
        count = numbers.attributive(numbers.cardinal(num, profile), word, profile)
        return f"{count} {word}"

    def mixed_replace(match: re.Match[str]) -> str:
        out = spoken(*_UNICODE_FRACTIONS[match.group("frac")])
        if not out:
            return match.group(0)
        whole = numbers.number_token(match.group("whole"), profile)
        return f"{whole} {profile.and_word} {out}"

    def unicode_replace(match: re.Match[str]) -> str:
        out = spoken(*_UNICODE_FRACTIONS[match.group(0)])
        return f" {out}" if out else match.group(0)

    def ascii_replace(match: re.Match[str]) -> str:
        out = spoken(int(match.group("num")), int(match.group("den")))
        return out if out else match.group(0)

    text = rules.mixed_fraction.sub(mixed_replace, text)
    text = rules.unicode_fraction.sub(unicode_replace, text)
    return rules.ascii_fraction.sub(ascii_replace, text)


def normalize_times(text: str, profile: LanguageProfile) -> str:
    """Give a colon-separated clock or verse reference speakable spacing."""
    if not text or ":" not in text:
        return text

    def replace(match: re.Match[str]) -> str:
        parts = [numbers.cardinal(int(match.group("h")), profile)]
        parts.append(numbers.digit_pair(match.group("m"), profile))
        if match.group("s"):
            parts.append(numbers.digit_pair(match.group("s"), profile))
        return " ".join(parts)

    return _rules(profile).clock.sub(replace, text)


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------


def normalize_numbers(text: str, profile: LanguageProfile) -> str:
    rules = _rules(profile)

    def roman_decimal(match: re.Match[str]) -> str:
        value = roman_to_int(match.group("roman"))
        if value is None:
            return match.group(0)
        parts = [numbers.cardinal(value, profile)]
        for piece in match.group("num").split("."):
            parts.append(
                numbers.cardinal(int(piece), profile) if piece.isdigit() else piece
            )
        return f" {profile.decimal_word} ".join(parts)

    def label_number(match: re.Match[str]) -> str:
        parts = [
            numbers.cardinal(int(piece), profile) if piece.isdigit() else piece
            for piece in match.group("num").split(".")
        ]
        joined = f" {profile.decimal_word} ".join(parts)
        return f"{match.group('label')} {joined}"

    def grouped(match: re.Match[str]) -> str:
        token = match.group(0).replace(profile.thousands_sep, "")
        return numbers.cardinal(int(token), profile) if token.isdigit() else match.group(0)

    def decimal(match: re.Match[str]) -> str:
        parts = match.group(0).split(profile.decimal_sep)
        if len(parts) == 2:
            return numbers.decimal(parts[0], parts[1], profile)
        return f" {profile.decimal_word} ".join(
            numbers.number_token(part, profile) for part in parts
        )

    def dotted_run_words(match: re.Match[str]) -> str:
        return f" {profile.decimal_word} ".join(
            numbers.number_token(part, profile)
            for part in match.group(0).split(".")
        )

    def signed(match: re.Match[str]) -> str:
        word = numbers.cardinal(int(match.group("num")), profile)
        prefix = profile.minus_word if match.group("sign") == "-" else profile.plus_word
        return f"{prefix} {word}"

    def decade(match: re.Match[str]) -> str:
        token = match.group("num")
        value = int(token)
        if len(token) == 4 and not token.startswith("0") and 1000 <= value <= 2099:
            spoken = numbers.year(value, profile)
        else:
            spoken = numbers.number_token(token, profile)
        return profile.decade_form(spoken) if profile.decade_form else spoken

    def year_range(match: re.Match[str]) -> str:
        start = int(match.group("start"))
        end = _expand_range_end(start, match.group("end"))
        if end is None or not (1000 <= end <= 2099):
            return match.group(0)
        start_words = numbers.year(start, profile)
        return f"{start_words} {profile.range_word} {numbers.year(end, profile)}"

    def plain_year(match: re.Match[str]) -> str:
        return numbers.year(int(match.group("year")), profile)

    def month_ordinal(match: re.Match[str]) -> str:
        spoken = numbers.ordinal(int(match.group("num")), profile)
        prev = text[: match.start()].rstrip().rsplit(" ", 1)[-1].lower()
        if prev in profile.month_dative_preps:
            spoken += "n"
        return f"{spoken} {match.group('month')}"

    text = rules.roman_decimal.sub(roman_decimal, text)
    if rules.label_number is not None:
        text = rules.label_number.sub(label_number, text)
    text = rules.grouped_int.sub(grouped, text)
    text = rules.decimal.sub(decimal, text)
    # A dotted run the thousands rule rejected ("1.2" in German) still needs a
    # spoken separator, or its dot reads to the chunker as a sentence end.
    text = rules.dotted_run.sub(dotted_run_words, text)
    text = rules.signed_int.sub(signed, text)
    if rules.decade is not None:
        text = rules.decade.sub(decade, text)
    text = rules.year_range.sub(year_range, text)
    if rules.month_ordinal is not None:
        text = rules.month_ordinal.sub(month_ordinal, text)
    text = rules.year.sub(plain_year, text)
    text = normalize_ordinals(text, profile)
    return _normalize_residual_digits(text, profile)


def normalize_ordinals(text: str, profile: LanguageProfile) -> str:
    """Rewrite each language's ordinal markers: "1st", "1.", "1º", "1er"."""
    for pattern in _rules(profile).ordinals:
        text = pattern.sub(
            lambda m: numbers.ordinal(
                int(m.group("num")),
                profile,
                feminine=bool(m.groupdict().get("fem")),
            ),
            text,
        )
    return text


def _expand_range_end(start: int, end_raw: str) -> int | None:
    token = end_raw.strip()
    if not token.isdigit():
        return None
    if len(token) == 2:
        year = (start // 100) * 100 + int(token)
        return year + 100 if year < start else year
    if len(token) == 4:
        return int(token)
    return None


def _normalize_residual_digits(text: str, profile: LanguageProfile) -> str:
    """Spell out every digit run left over, keeping words from fusing."""
    if not text:
        return text
    parts: list[str] = []
    cursor = 0
    length = len(text)
    for match in _RESIDUAL_DIGITS_RE.finditer(text):
        start, end = match.span()
        if cursor < start:
            parts.append(text[cursor:start])
        left = text[start - 1] if start > 0 else ""
        right = text[end] if end < length else ""
        if left.isalpha() and (not parts or not parts[-1].endswith(" ")):
            parts.append(" ")
        parts.append(numbers.number_token(match.group(0), profile))
        if right.isalpha():
            parts.append(" ")
        cursor = end
    if cursor < length:
        parts.append(text[cursor:])
    return "".join(parts)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def normalize_lexical(text: str, profile: LanguageProfile) -> str:
    """Run the full lexical pipeline for one language."""
    for hook in profile.pre_hooks:
        text = hook(text)
    text = normalize_abbreviations(text, profile)
    text = normalize_eras(text, profile)
    text = normalize_roman_numerals(text, profile)
    text = normalize_currency(text, profile)
    text = normalize_quantities(text, profile)
    text = normalize_symbols(text, profile)
    text = normalize_fractions(text, profile)
    text = normalize_times(text, profile)
    text = normalize_numbers(text, profile)
    for hook in profile.post_hooks:
        text = hook(text)
    return text
