"""End-to-end integration tests that drive neb's synth pipeline with synthetic data.

These tests intentionally do not mock pocket-tts. They exercise every step of the
neb pipeline — manifest prep, chunking, voice resolution, model load, audio
generation, wav writing — so regressions in any layer (including pocket-tts
version bumps and new model-config flags) surface in CI.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from neb import tts

pocket_tts_available = tts.TTSModel is not None and tts.torch is not None
requires_pocket_tts = pytest.mark.skipif(
    not pocket_tts_available,
    reason="pocket-tts runtime not available (run via ./bin/pmx)",
)


@requires_pocket_tts
@pytest.mark.parametrize(
    "language, layers, text",
    [
        ("english", 6, "Hello world."),
        ("german", 24, "Guten Tag."),
    ],
)
def test_synthesize_produces_wav_end_to_end(
    tmp_path: Path, language: str, layers: int, text: str
) -> None:
    chapter = tts.ChapterInput(
        index=1,
        id="0001-smoke",
        title="Smoke",
        text=text,
        path=None,
    )
    out_dir = tmp_path / "tts"

    rc = tts.synthesize(
        chapters=[chapter],
        voice="alba",
        out_dir=out_dir,
        max_chars=200,
        pad_ms=100,
        chunk_mode="sentence",
        rechunk=True,
        base_dir=tmp_path,
        language=language,
        layers=layers,
    )
    assert rc == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["language"] == language
    assert manifest["layers"] == layers
    assert manifest["voice"] == "alba"

    seg_path = out_dir / "segments" / chapter.id / "000001.wav"
    assert seg_path.exists(), f"expected wav at {seg_path}"
    assert seg_path.stat().st_size > 0

    chapter_entry = manifest["chapters"][0]
    durations = chapter_entry["durations_ms"]
    assert durations and durations[0] and durations[0] > 0
