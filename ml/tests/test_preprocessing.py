import pandas as pd
import pytest

from orientation_ml.preprocessing.pipeline import make_preprocessor


def test_record_id_and_target_are_not_features():
    frame = pd.DataFrame({"record_id": ["a"], "target_field_code": ["REAL"], "score_math": [12.0]})
    _, features = make_preprocessor(frame)
    assert features == ["score_math"]


def test_pii_cannot_be_a_feature():
    with pytest.raises(ValueError, match="PII"):
        make_preprocessor(pd.DataFrame({"email": ["x@example.test"], "target_field_code": ["REAL"]}))

