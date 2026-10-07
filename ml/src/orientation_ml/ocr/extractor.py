import json
import re
import uuid
from pathlib import Path

from ..paths import data_path
from ..utils.hashing import sha256_file
from .document_reader import read_document
from .score_parser import parse_scores


def extract_graduation_year(text: str) -> int | None:
    """Only take a year explicitly tied to an exam/session label, never a birth date."""
    match = re.search(r"\b(?:année|annee|session|graduation|year)\b[^\d]{0,20}(20\d{2})\b", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_series(text: str) -> str | None:
    match = re.search(r"\b(?:série|serie|option)\s*[:\-]?\s*([A-D])\b", text, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _extract_average(text: str) -> float | None:
    match = re.search(r"\b(?:moyenne|average)\b[^\d\n]{0,20}(\d{1,2}(?:[.,]\d{1,2})?)", text, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    return value if 0 <= value <= 20 else None


def _extract_mention(text: str) -> str | None:
    match = re.search(r"\b(passable|assez\s+bien|bien|très\s+bien|tres\s+bien|excellent)\b", text, re.IGNORECASE)
    if not match:
        return None
    return " ".join(word.capitalize() for word in match.group(1).split())


def find_existing_record(source_sha256: str) -> dict | None:
    """Return the existing extraction record for an identical source file."""
    directory = data_path("extracted_dir")
    if not directory.exists():
        return None
    for record_path in sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("source_sha256") == source_sha256:
            return record
    return None


def extract(path: Path, *, force: bool = False) -> dict:
    path = Path(path)
    source_sha256 = sha256_file(path)
    if not force:
        existing = find_existing_record(source_sha256)
        if existing:
            return existing
    document = read_document(path)
    try:
        scores, warnings = parse_scores(document.text)
    except ValueError as exc:
        detail = " ".join(document.warnings)
        suffix = f" {detail}" if detail else " Vérifiez la qualité et l'orientation du document, puis les alias de matières."
        raise ValueError(f"{exc}{suffix}") from exc
    series = _extract_series(document.text)
    graduation_year = extract_graduation_year(document.text)
    average = _extract_average(document.text)
    mention = _extract_mention(document.text)
    record_id = uuid.uuid4().hex
    record = {
        "record_id": record_id,
        "source_sha256": source_sha256,
        "extraction_version": "2.0",
        "bac_series": series,
        "graduation_year": graduation_year,
        "scores": {score.subject: {"raw_subject": score.raw_subject, "raw_score": score.raw_score,
                                   "max_score": score.max_score, "normalized_score": score.normalized_score,
                                   "coefficient": score.coefficient, "optional": score.optional,
                                   "confidence": score.confidence, "warning": score.warning} for score in scores},
        "average_score": average,
        "mention": mention,
        "target_field_code": None,
        "validated": False,
        "ocr_used": document.ocr_used,
        "ocr_engine": document.ocr_engine,
        "pages": document.pages,
        "warnings": warnings + document.warnings,
    }
    output = data_path("extracted_dir")
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{record_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / f"{record_id}.txt").write_text(document.text, encoding="utf-8")
    return record

