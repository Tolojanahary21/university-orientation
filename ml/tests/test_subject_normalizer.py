from orientation_ml.ocr.subject_normalizer import normalize_subject


def test_accent_and_alias_normalization():
    result = normalize_subject("  MATHEMATIQUES  ")
    assert result["canonical_subject"] == "mathematics"
    assert result["confidence"] == 1


def test_rejects_weak_fuzzy_match():
    assert normalize_subject("zzzzzz") is None

