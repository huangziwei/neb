"""Number → words, for every supported language, via num2words.

num2words already knows each language's cardinals, ordinals, and year forms
(including French 70/80/90, Italian vowel elision, and the German -te/-ste
split), so this module only adapts its output to what the TTS models want:

  * `profile.number_tidy` reshapes punctuation — English drops the commas,
    hyphens, and "and" that num2words inserts;
  * `attributive` supplies the pre-nominal form of "one", so German reads
    "ein Euro" rather than the standalone "eins Euro".

Results are cached because a chapter repeats the same handful of numbers many
times over.
"""
from __future__ import annotations

from functools import lru_cache

from num2words import num2words

from .profile import LanguageProfile


def _convert(value: int, lang: str, to: str) -> str | None:
    try:
        return num2words(value, lang=lang, to=to)
    except (NotImplementedError, OverflowError, TypeError, ValueError, KeyError):
        return None


@lru_cache(maxsize=4096)
def _cached(value: int, lang: str, to: str) -> str | None:
    return _convert(value, lang, to)


def _tidy(spoken: str | None, profile: LanguageProfile) -> str | None:
    if spoken is None:
        return None
    if profile.number_tidy is not None:
        spoken = profile.number_tidy(spoken)
    return spoken.strip()


def cardinal(value: int, profile: LanguageProfile) -> str:
    """Spoken cardinal, or the plain digits if the language cannot form one."""
    spoken = _tidy(_cached(value, profile.n2w_lang, "cardinal"), profile)
    return spoken or str(value)


def ordinal(value: int, profile: LanguageProfile, *, feminine: bool = False) -> str:
    """Spoken ordinal. Falls back to the cardinal when unavailable."""
    spoken = _tidy(_cached(value, profile.n2w_lang, "ordinal"), profile)
    if not spoken:
        return cardinal(value, profile)
    if feminine and profile.ordinal_feminine is not None:
        return profile.ordinal_feminine(spoken)
    return spoken


def year(value: int, profile: LanguageProfile) -> str:
    """Spoken year. Languages that read years as plain cardinals get that."""
    spoken = _tidy(_cached(value, profile.n2w_lang, "year"), profile)
    return spoken or cardinal(value, profile)


def digit_string(token: str, profile: LanguageProfile) -> str:
    """Read a run digit by digit — for leading zeros and reference codes."""
    parts: list[str] = []
    for ch in token:
        parts.append(cardinal(int(ch), profile) if ch.isdigit() else ch)
    return " ".join(parts)


def number_token(token: str, profile: LanguageProfile) -> str:
    """Spoken form of a bare digit run, reading leading zeros one by one."""
    if not token:
        return token
    if len(token) > 1 and token.startswith("0"):
        return digit_string(token, profile)
    try:
        value = int(token)
    except ValueError:
        return digit_string(token, profile)
    return cardinal(value, profile)


def digit_pair(token: str, profile: LanguageProfile) -> str:
    """Read a two-digit group as one unit: '05' → English 'oh five'."""
    if len(token) == 2 and token.startswith("0") and profile.pair_zero_word:
        return f"{profile.pair_zero_word} {cardinal(int(token[1]), profile)}"
    return number_token(token, profile)


def decimal(int_part: str, frac_part: str, profile: LanguageProfile) -> str:
    """'3.85' → 'three point eight five'; the fraction is read digit by digit."""
    left = number_token(int_part or "0", profile)
    right = digit_string(frac_part, profile)
    return f"{left} {profile.decimal_word} {right}"


def attributive(spoken: str, noun: str, profile: LanguageProfile) -> str:
    """Adjust a trailing 'one' to the form used before a noun.

    German "eins" → "ein Euro"; Spanish "veintiuno" → "veintiún euros";
    Italian "ventuno" → "ventun euro". Languages whose numeral does not change
    before a noun are returned untouched.
    """
    replacement = profile.attributive_one
    if not replacement:
        return spoken
    standalone = cardinal(1, profile)
    if not spoken.endswith(standalone):
        return spoken
    if noun in profile.feminine_nouns and profile.attributive_one_feminine:
        replacement = profile.attributive_one_feminine
    return spoken[: -len(standalone)] + replacement
