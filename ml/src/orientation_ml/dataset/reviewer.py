import json
from pathlib import Path

from ..paths import data_path
from .validator import validate_record


def _edit(prompt: str, current):
    value = input(f"{prompt} [{current if current is not None else ''}]: ").strip()
    return current if not value else value


def review(record_id: str) -> Path:
    source = data_path("extracted_dir") / f"{record_id}.json"
    record = json.loads(source.read_text(encoding="utf-8"))
    record["bac_series"] = _edit("Série", record.get("bac_series")) or None
    year = _edit("Année du bac", record.get("graduation_year"))
    record["graduation_year"] = int(year) if year else None
    for subject, score in record["scores"].items():
        print(f"\n{subject} — {score['raw_subject']} (normalisé {score['normalized_score']}/20)")
        score["raw_score"] = float(_edit("Note brute", score["raw_score"]).replace(",", "."))
        score["max_score"] = float(_edit("Note maximale", score["max_score"]).replace(",", "."))
        coefficient = _edit("Coefficient (vide = inconnu)", score.get("coefficient"))
        score["coefficient"] = float(coefficient.replace(",", ".")) if coefficient else None
        if score["max_score"] > 0:
            score["normalized_score"] = round(score["raw_score"] * 20 / score["max_score"], 2)
        score["warning"] = None if score["max_score"] > 0 and 0 <= score["raw_score"] <= score["max_score"] else "Valeurs invalides; vérification requise"
        print(f"Note normalisée recalculée: {score['normalized_score']}/20")
    average = _edit("Moyenne officielle", record.get("average_score"))
    record["average_score"] = float(average.replace(",", ".")) if average else None
    record["mention"] = _edit("Mention", record.get("mention")) or None
    print("Warnings:", "; ".join(record.get("warnings", [])) or "aucun")
    if input("Valider ce relevé ? [o/N] ").strip().lower() != "o":
        raise ValueError("Validation annulée")
    target = input("target_field_code (annotation humaine) : ").strip()
    record["validated"] = False
    record["target_field_code"] = None
    validated = validate_record(record, target)
    output = data_path("validated_dir")
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"{record_id}.json"
    destination.write_text(json.dumps(validated, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination
