from src.langs import LANGUAGES


def test_all_languages_share_same_keys():
    languages = list(LANGUAGES.keys())
    assert languages, "No languages defined"

    keys0 = set(LANGUAGES[languages[0]].keys())
    for lang in languages[1:]:
        assert set(LANGUAGES[lang].keys()) == keys0, f"Key mismatch for language: {lang}"


def test_required_translation_keys_exist():
    required = {
        "currency_label",
        "upload_msg",
        "fx_rate_msg",
        "sidebar_settings",
        "sidebar_market",
        "sidebar_import",
        "tab_visuals",
        "tab_data",
        "tab_earnings",
        "tab_audit",
    }

    for lang, texts in LANGUAGES.items():
        missing = required - set(texts.keys())
        assert not missing, f"{lang} missing keys: {sorted(missing)}"
