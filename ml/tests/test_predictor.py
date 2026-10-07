import pytest

from orientation_ml.inference.predictor import ModelNotTrained, predict


def test_missing_model_is_clear(tmp_path):
    with pytest.raises(ModelNotTrained):
        predict({"scores": {}}, model_path=tmp_path / "missing.joblib")

