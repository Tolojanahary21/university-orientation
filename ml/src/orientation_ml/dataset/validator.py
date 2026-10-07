from ..paths import load_yaml
from .schema import ExtractedRecord


class InvalidTrainingRecord(ValueError):
    pass


class UnknownFieldCode(ValueError):
    pass


def validate_record(record: dict, target_field_code: str) -> dict:
    parsed = ExtractedRecord.model_validate(record)
    if not parsed.scores:
        raise InvalidTrainingRecord("Aucune matière extraite")
    for subject, score in parsed.scores.items():
        if score.max_score <= 0 or score.raw_score < 0 or score.raw_score > score.max_score:
            raise InvalidTrainingRecord(f"Valeurs de note invalides pour {subject}")
        if score.warning:
            raise InvalidTrainingRecord(f"Correction humaine requise pour {subject}: {score.warning}")
        expected = round(score.raw_score * 20 / score.max_score, 2)
        if abs(expected - score.normalized_score) > 0.02:
            raise InvalidTrainingRecord(f"Note normalisée incohérente pour {subject}")
    if parsed.average_score is not None and not 0 <= parsed.average_score <= 20:
        raise InvalidTrainingRecord("Moyenne officielle hors intervalle")
    if len(parsed.scores) < load_yaml("data.yaml").get("minimum_subjects", 3):
        raise InvalidTrainingRecord("Nombre minimum de matières non atteint")
    valid_codes = set(load_yaml("labels.yaml").get("target_fields", []))
    if not valid_codes or target_field_code not in valid_codes:
        raise UnknownFieldCode(f"Code filière inconnu: {target_field_code!r}. Configurez labels.yaml depuis backend/fields.")
    return {**parsed.model_dump(), "validated": True, "validated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "target_field_code": target_field_code}

