import json

import pandas as pd

from ..paths import data_path, load_yaml
from .validator import validate_record

SUBJECTS = list(load_yaml("subjects.yaml"))
PII_KEYS = {"name", "first_name", "last_name", "student_name", "email", "phone", "address", "matricule"}


def build_dataset() -> pd.DataFrame:
    source, output = data_path("validated_dir"), data_path("raw_dir")
    output.mkdir(parents=True, exist_ok=True)
    rows, seen_hashes = [], set()
    for path in sorted(source.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if PII_KEYS.intersection(record):
            raise ValueError(f"PII détectée dans {path.name}; dataset non écrit")
        validate_record(record, record.get("target_field_code", ""))
        if record["source_sha256"] in seen_hashes:
            continue
        seen_hashes.add(record["source_sha256"])
        row = {"record_id": record["record_id"], "bac_series": record.get("bac_series"), "average_score": record.get("average_score"), "mention": record.get("mention")}
        row.update({f"score_{subject}": record.get("scores", {}).get(subject, {}).get("normalized_score") for subject in SUBJECTS})
        row[load_yaml("data.yaml")["target_column"]] = record["target_field_code"]
        rows.append(row)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_csv(output / "orientation_dataset.csv", index=False)
        try:
            frame.to_parquet(output / "orientation_dataset.parquet", index=False)
        except ImportError:
            pass
    return frame

