"""The per-language data record that drives every lexical transform.

A profile holds only data; the machinery consuming it lives in `engine`.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

# (singular, plural) spoken forms. Languages whose noun does not inflect after
# a numeral (German "10 Euro") simply repeat the same string.
SpokenNoun = tuple[str, str]

TextHook = Callable[[str], str]


@dataclass(frozen=True, eq=False)
class LanguageProfile:
    """Everything `engine` needs to normalize one language."""

    name: str

    # --- number → words -----------------------------------------------------
    # `n2w_lang` is the num2words language code; `number_tidy` reshapes its
    # output to the punctuation-free style the TTS models read best.
    n2w_lang: str
    decimal_word: str
    minus_word: str
    plus_word: str
    range_word: str
    # Joins the whole and fractional halves of a mixed number: "1½" → "one and a half".
    and_word: str = "and"
    number_tidy: TextHook | None = None
    # Written conventions: which character groups thousands and which marks the
    # decimal. English is ("," "."); the other five are ("." ",").
    thousands_sep: str = ","
    decimal_sep: str = "."
    # Filler spoken for a leading zero inside a two-digit pair — English
    # "five oh five". Languages that read the plain cardinal leave it None.
    pair_zero_word: str | None = None
    # The form "one" takes directly before a noun: German "ein Euro" rather
    # than the standalone "eins". None where the numeral does not change.
    attributive_one: str | None = None
    attributive_one_feminine: str | None = None
    # Currency, scale, and unit nouns that select the feminine numeral.
    feminine_nouns: frozenset = frozenset()

    # --- script -------------------------------------------------------------
    # Precomposed characters this language owns; the rest folds to ASCII.
    native_letters: frozenset = frozenset()
    # Spell Pali and Sanskrit letters the way the model can say them ("ā" → "aa").
    transliterate_indic: bool = False

    # --- currency and magnitude --------------------------------------------
    currency_units: Mapping[str, SpokenNoun] = field(default_factory=dict)
    # Magnitude words that may sit between an amount and its noun, spelled or
    # abbreviated: {"billion": ("billion", "billion"), "bn": (...)}. Lookup is
    # case-insensitive and a trailing dot is ignored, so "Mrd." finds "mrd".
    scale_words: Mapping[str, SpokenNoun] = field(default_factory=dict)
    # Magnitude abbreviations too ambiguous to honour on their own — English
    # "20 m" is metres — so they count only directly against a currency symbol.
    scale_abbrevs: Mapping[str, SpokenNoun] = field(default_factory=dict)
    # Romance languages link a magnitude noun to its unit with a preposition:
    # "due milioni di euro", "deux milliards de dollars". The thousand words are
    # numeral adjectives, not nouns, so they are exempt ("duemila euro").
    scale_preposition: str | None = None
    scale_preposition_exempt: frozenset = frozenset()

    # --- symbols ------------------------------------------------------------
    # Symbols that attach to an amount and inflect with it ("1 degree" /
    # "5 degrees"): {"%": ("percent", "percent")}.
    symbol_units: Mapping[str, SpokenNoun] = field(default_factory=dict)
    # Temperature scale letters following a degree sign: {"C": "Celsius"}.
    degree_scales: Mapping[str, str] = field(default_factory=dict)
    # Standalone symbols with one invariant reading, spoken between spaces.
    symbol_words: Mapping[str, str] = field(default_factory=dict)
    # Denominator → (singular, plural): 2 → ("half", "halves") gives "one half"
    # and "three halves". An absent denominator leaves the fraction untouched.
    fraction_denominators: Mapping[int, SpokenNoun] = field(default_factory=dict)

    # --- headings and labels ------------------------------------------------
    # Words that take a dotted section number: "Figure 1.2" → "Figure one point two".
    label_words: Sequence[str] = ()
    # Words that take a Roman numeral: "Chapter IV" → "Chapter four".
    roman_labels: Sequence[str] = ()
    # Conjunctions joining a list of numerals: "Chapters I, II and III".
    roman_list_joiners: Sequence[str] = ("and", "or")
    # English alone needs the pronoun "I" protected from becoming "one".
    guard_roman_i: bool = False
    roman_i_determiners: frozenset = frozenset()
    # Nouns proving a four-digit number is a quantity, not a year, so "1500 Euro"
    # stays cardinal. Currency and scale words are matched automatically; list
    # only the extras (units, measures).
    unit_words: Sequence[str] = ()

    # --- abbreviations ------------------------------------------------------
    # Literal multi-token forms replaced before anything else ("z. B.").
    multi_dot_abbrevs: Mapping[str, str] = field(default_factory=dict)
    # Stem (no trailing dot, lowercase) → expansion, matched case-insensitively
    # with the source capitalization preserved.
    abbrev_expansions: Mapping[str, str] = field(default_factory=dict)
    # Applied only when a number or Roman numeral follows, and spoken exactly as
    # written here: "No. 5" → "number five", "Nr. 5" → "Nummer fünf".
    numbered_abbrevs: Mapping[str, str] = field(default_factory=dict)
    # Kept as written but stripped of the dot, so the chunker sees no sentence
    # end: "Mr." → "Mr".
    dot_strip_abbrevs: Sequence[str] = ()
    # (pattern, replacement) pairs applied case-insensitively for era markers.
    era_replacements: Sequence[tuple[str, str]] = ()

    # --- ordinals and dates -------------------------------------------------
    # Regexes with a "num" group and an optional "fem" group; a matched "fem"
    # selects the feminine ordinal (Italian "1ª" → "prima").
    ordinal_patterns: Sequence[str] = ()
    ordinal_feminine: TextHook | None = None
    # Month names, for "3. Oktober" → "dritten Oktober". Empty disables the rule.
    month_words: Sequence[str] = ()
    # Prepositions after which a German date ordinal takes its dative -n.
    month_dative_preps: frozenset = frozenset()

    # --- decades ------------------------------------------------------------
    # Pattern with a "num" group matching a decade form ("1990s", "80er"), and
    # the transform from the spoken number to the decade word.
    decade_pattern: str | None = None
    decade_form: TextHook | None = None

    # --- escape hatches -----------------------------------------------------
    pre_hooks: Sequence[TextHook] = ()
    post_hooks: Sequence[TextHook] = ()
