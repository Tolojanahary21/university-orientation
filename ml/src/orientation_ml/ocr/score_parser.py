import re
from dataclasses import dataclass

from ..exceptions import NoScoresFound
from .subject_normalizer import normalize_subject_prefix


@dataclass
class ParsedScore:
    subject: str
    raw_subject: str
    raw_score: float
    max_score: float
    normalized_score: float
    coefficient: float | None
    optional: bool
    confidence: float
    warning: str | None = None

    @property
    def value(self) -> float:
        """Compatibility alias for callers that used the old /20 field."""
        return self.normalized_score


NUMBER = re.compile(r"(?<![A-Za-z])(?:\d|[Oo]){1,3}(?:[.,](?:\d|[Oo]){1,2})?(?![A-Za-z])")
NON_SUBJECT_MARKERS = re.compile(r"\b(?:boni|facultative|optionnelle?)\b", re.IGNORECASE)


def _number(token: str) -> float:
    # OCR often confuses O with zero in numeric table cells. Only numeric tokens
    # are corrected, so words in subject names are untouched.
    return float(token.replace("O", "0").replace("o", "0").replace(",", "."))


def _raw_subject(line: str) -> tuple[str, dict | None]:
    match = NUMBER.search(line)
    label = line[: match.start()] if match else line
    label = NON_SUBJECT_MARKERS.sub(" ", label).strip(" :-|\t")
    return label, normalize_subject_prefix(label)


def parse_scores(text: str) -> tuple[list[ParsedScore], list[str]]:
    scores: list[ParsedScore] = []
    warnings: list[str] = []
    table_has_max_column = bool(re.search(r"\bnote\s+max\b", text, re.IGNORECASE))
    seen: set[str] = set()
    for line in text.splitlines():
        label, subject = _raw_subject(line)
        if not subject:
            # Preserve clearly numeric OCR rows for the position-based review
            # and avoid assigning them to a different subject by row order.
            continue
        canonical = subject["canonical_subject"]
        values = [_number(value) for value in NUMBER.findall(line)]
        optional = bool(re.search(r"\b(?:boni|facultative|optionnelle?)\b", line, re.IGNORECASE))
        if len(values) == 1 and not table_has_max_column and 0 <= values[0] <= 20:
            raw_score, max_score, coefficient = values[0], 20.0, None
        elif len(values) < 2:
            warnings.append(f"Note ou maximum manquant pour {canonical}; vérification humaine requise")
            continue
        else:
            coefficient = None
            if len(values) >= 3:
                coefficient, raw_score, max_score = values[-3:]
            elif optional and len(values) == 2:
                raw_score, max_score = values
            elif not table_has_max_column:
                raw_score, max_score = values[-2:]
            else:
                warnings.append(f"Ligne ambiguë sans coefficient identifiable pour {canonical}; vérification humaine requise")
                continue

        row_warnings = []
        if max_score <= 0:
            row_warnings.append("maximum doit être supérieur à zéro")
            normalized = None
        else:
            normalized = round(raw_score * 20 / max_score, 2)
        if raw_score < 0 or raw_score > max_score:
            row_warnings.append("note brute hors limites")
        if normalized is not None and not 0 <= normalized <= 20:
            row_warnings.append("note normalisée hors limites")
        if canonical in seen:
            warnings.append(f"Plusieurs lignes reconnues pour {canonical}; vérification humaine requise")
        seen.add(canonical)
        warning = "; ".join(row_warnings) or None
        if warning:
            warnings.append(f"{canonical}: {warning}; vérification humaine requise")
        scores.append(ParsedScore(canonical, label, raw_score, max_score, normalized if normalized is not None else 0.0,
                                  coefficient, optional, subject["confidence"], warning))

    if not scores:
        raise NoScoresFound("Aucune note reconnue. Vérifiez la qualité et l'orientation du document ainsi que les alias de matières.")
    return scores, warnings
