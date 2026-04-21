import pytest

from neb import language


def test_normalize_defaults_when_missing() -> None:
    assert language.normalize_language_tag(None) == "english"
    assert language.normalize_language_tag("") == "english"
    assert language.normalize_language_tag("   ") == "english"


def test_normalize_accepts_pocket_tts_names() -> None:
    for name in language.POCKET_TTS_LANGUAGES:
        assert language.normalize_language_tag(name) == name
        assert language.normalize_language_tag(name.upper()) == name


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("en", "english"),
        ("eng", "english"),
        ("en-US", "english"),
        ("en_GB", "english"),
        ("de", "german"),
        ("de-DE", "german"),
        ("deu", "german"),
        ("fr-CA", "french"),
        ("pt-BR", "portuguese"),
        ("es-419", "spanish"),
        ("it", "italian"),
    ],
)
def test_normalize_maps_iso_codes(tag: str, expected: str) -> None:
    assert language.normalize_language_tag(tag) == expected


def test_normalize_rejects_unsupported_language() -> None:
    with pytest.raises(language.UnsupportedLanguageError):
        language.normalize_language_tag("ja")
    with pytest.raises(language.UnsupportedLanguageError):
        language.normalize_language_tag("zh-Hans")


def test_display_name_capitalizes() -> None:
    assert language.display_name("german") == "German"
    assert language.display_name("english") == "English"
    assert language.display_name("") == ""
    assert language.display_name(None) == ""
