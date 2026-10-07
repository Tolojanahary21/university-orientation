import pytest

from orientation_ml.dataset.schema import Score, ValidatedRecord


def test_scores_must_be_on_twenty():
    with pytest.raises(ValueError):
        Score(value=21)


def test_validated_record_requires_target():
    with pytest.raises(ValueError):
        ValidatedRecord(record_id="x", source_sha256="a", extraction_version="1", scores={}, validated=True, validated_at="now", target_field_code="")

