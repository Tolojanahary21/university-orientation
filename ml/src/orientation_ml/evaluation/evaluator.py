import json

import joblib
import pandas as pd

from ..paths import data_path, load_yaml
from .metrics import classification_metrics


def evaluate() -> dict:
    model = joblib.load(data_path("root_dir") / "models" / "orientation_model.joblib")
    test = pd.read_csv(data_path("splits_dir") / "test.csv")
    target = load_yaml("data.yaml")["target_column"]
    X, y = test.drop(columns=[target, "record_id"]), test[target]
    metrics = classification_metrics(model, X, y, top_k=load_yaml("training.yaml")["top_k"])
    output = data_path("root_dir") / "reports" / "metrics"
    output.mkdir(parents=True, exist_ok=True)
    (output / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics

