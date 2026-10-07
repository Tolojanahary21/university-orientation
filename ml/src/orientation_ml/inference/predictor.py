from pathlib import Path

import joblib

from ..dataset.schema import PredictionInput
from ..paths import data_path, load_yaml
from .feature_adapter import to_frame


class ModelNotTrained(RuntimeError):
    pass


class FeatureSchemaMismatch(RuntimeError):
    pass


def predict(payload: dict, top_k: int | None = None, model_path: Path | None = None) -> list[dict]:
    parsed = PredictionInput.model_validate(payload)
    artifact = model_path or data_path("root_dir") / "models" / "orientation_model.joblib"
    if not artifact.exists():
        raise ModelNotTrained("Aucun modèle entraîné n'est disponible.")
    model = joblib.load(artifact)
    frame = to_frame(parsed.model_dump())
    model_pipeline = model
    expected = getattr(model_pipeline, "feature_names_in_", None)
    if expected is not None and not set(expected).issubset(frame.columns):
        raise FeatureSchemaMismatch("Les features de la requête ne correspondent pas au modèle.")
    probabilities = model.predict_proba(frame)[0]
    classes = list(model.classes_)
    if not set(classes).issubset(set(load_yaml("labels.yaml").get("target_fields", []))):
        raise FeatureSchemaMismatch("Le modèle contient des filières absentes de la configuration labels.yaml.")
    limit = top_k or load_yaml("training.yaml")["top_k"]
    ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)[:limit]
    return [{"field_code": code, "probability": float(probability), "rank": rank} for rank, (code, probability) in enumerate(ranked, 1)]

