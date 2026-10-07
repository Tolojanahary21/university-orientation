import pandas as pd

from ..paths import data_path, load_yaml


def check_dataset() -> list[str]:
    path = data_path("raw_dir") / "orientation_dataset.csv"
    if not path.exists():
        raise FileNotFoundError("Dataset absent. Ajoutez et validez de vrais relevés.")
    frame = pd.read_csv(path)
    errors = []
    target = load_yaml("data.yaml")["target_column"]
    if target not in frame or frame[target].isna().any():
        errors.append("target_field_code absent ou vide")
    prohibited = {"name", "first_name", "last_name", "student_name", "email", "phone", "address", "matricule"}
    if prohibited.intersection(column.casefold() for column in frame.columns):
        errors.append("colonnes PII interdites présentes")
    if frame.record_id.duplicated().any():
        errors.append("record_id dupliqué")
    return errors

