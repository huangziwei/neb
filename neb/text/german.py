"""German-specific lexical normalization for TTS.

Stage B will populate this with: number-to-words (with tens/ones reversal,
e.g. "einundvierzig"), year pronunciation ("neunzehnhundertfünfundachtzig"),
ordinals, abbreviation expansion (Dr./Hr./Fr./Prof./Nr./S./z. B./d. h./
usw./bzw./ca.), currency (Dollar/Euro/Pfund — no plural -s), era markers
(v. Chr./n. Chr.), and Roman heading labels (Kapitel/Buch/Teil/Band/
Abschnitt/Akt/Szene/Anhang).

For now this is a pass-through — pocket-tts's German acoustic model handles
raw digits and dotted abbreviations better than English-rule normalization
would.
"""
from __future__ import annotations


def normalize_german_lexical(text: str) -> str:
    return text
