import re
import unicodedata

from rapidfuzz import fuzz, process

from ..paths import load_yaml


def _clean(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def normalize_subject(raw_subject: str, threshold: int = 84) -> dict | None:
    mapping = load_yaml("subjects.yaml")
    aliases = {}
    for canonical, config in mapping.items():
        aliases[_clean(canonical)] = canonical
        aliases.update({_clean(alias): canonical for alias in config.get("aliases", [])})
    cleaned = _clean(raw_subject)
    if cleaned in aliases:
        return {"canonical_subject": aliases[cleaned], "confidence": 1.0, "raw_subject": raw_subject}
    match = process.extractOne(cleaned, aliases.keys(), scorer=fuzz.ratio)
    if match and match[1] >= threshold:
        return {"canonical_subject": aliases[match[0]], "confidence": match[1] / 100, "raw_subject": raw_subject}
    return None


def normalize_subject_prefix(raw_subject: str) -> dict | None:
    """Match a known subject at the start of a table row, allowing trailing columns."""
    mapping = load_yaml("subjects.yaml")
    aliases = {}
    for canonical, config in mapping.items():
        aliases[_clean(canonical)] = canonical
        aliases.update({_clean(alias): canonical for alias in config.get("aliases", [])})
    cleaned = _clean(raw_subject)
    for alias in sorted(aliases, key=len, reverse=True):
        if cleaned == alias or cleaned.startswith(f"{alias} ") or alias.startswith(f"{cleaned} "):
            return {"canonical_subject": aliases[alias], "confidence": 1.0, "raw_subject": raw_subject}
    return normalize_subject(cleaned)

