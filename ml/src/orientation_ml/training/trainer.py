import json
import platform
import subprocess

import joblib
import pandas as pd
import sklearn

from ..dataset.quality import check_dataset
from ..paths import data_path, load_yaml
from ..utils.hashing import sha256_file
from .candidates import candidate_models
from .model_selection import select_champion


class ClassTooSmall(ValueError):
    pass


class DatasetTooSmall(ValueError):
    pass


def train() -> dict:
    if not (data_path("raw_dir") / "orientation_dataset.csv").exists():
        raise DatasetTooSmall("Dataset réel insuffisant pour l'entraînement.")
    errors = check_dataset()
    if errors:
        raise ValueError("Dataset invalide: " + "; ".join(errors))
    split_dir, raw_path = data_path("splits_dir"), data_path("raw_dir") / "orientation_dataset.csv"
    if not (split_dir / "train.csv").exists():
        from ..dataset.splitter import split_dataset
        split_dataset()
    train_frame = pd.read_csv(split_dir / "train.csv")
    valid = pd.read_csv(split_dir / "validation.csv")
    target = load_yaml("data.yaml")["target_column"]
    cfg = load_yaml("training.yaml")
    counts = train_frame[target].value_counts()
    if len(counts) < 2:
        raise DatasetTooSmall("Dataset réel insuffisant pour l'entraînement.")
    if (counts < cfg["minimum_examples_per_class"]).any():
        raise ClassTooSmall("Dataset réel insuffisant pour l'entraînement. Classes sous le minimum: " + ", ".join(f"{code}={count}" for code, count in counts.items() if count < cfg["minimum_examples_per_class"]))
    for code, count in counts.items():
        if count < cfg["low_data_warning_threshold"]:
            print(f"WARNING: faible quantité pour {code}: {count}")
    X_train, y_train = train_frame.drop(columns=[target, "record_id"]), train_frame[target]
    X_valid, y_valid = valid.drop(columns=[target, "record_id"]), valid[target]
    models = candidate_models(train_frame.drop(columns=[target, "record_id"]))
    for model in models.values():
        model.fit(X_train, y_train)
    champion = select_champion(models, X_valid, y_valid)
    destination = data_path("root_dir") / "models"
    destination.mkdir(parents=True, exist_ok=True)
    artifact = destination / "orientation_model.joblib"
    joblib.dump(models[champion], artifact)
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.SubprocessError):
        git_sha = None
    metadata = {"champion": champion, "dataset_sha256": sha256_file(raw_path), "feature_schema_version": load_yaml("data.yaml")["feature_schema_version"], "training_config": cfg, "python": platform.python_version(), "scikit_learn": sklearn.__version__, "git_sha": git_sha}
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"artifact": artifact, "metadata": metadata}

