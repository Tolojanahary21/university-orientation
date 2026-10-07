from pathlib import Path

import yaml

ML_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ML_ROOT.parent
CONFIG_DIR = ML_ROOT / "config"
DATA_DIR = ML_ROOT / "data"
SOURCE_DOCUMENTS_DIR = DATA_DIR / "source_documents"
EXTRACTED_DIR = DATA_DIR / "extracted"
VALIDATED_DIR = DATA_DIR / "validated"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_DIR = DATA_DIR / "splits"
REFERENCE_DIR = DATA_DIR / "reference"
MODELS_DIR = ML_ROOT / "models"
REPORTS_DIR = ML_ROOT / "reports"

_DATA_DIRS = {
    "documents_dir": SOURCE_DOCUMENTS_DIR,
    "extracted_dir": EXTRACTED_DIR,
    "validated_dir": VALIDATED_DIR,
    "raw_dir": RAW_DIR,
    "processed_dir": PROCESSED_DIR,
    "splits_dir": SPLITS_DIR,
    "reference_dir": REFERENCE_DIR,
}


def config_path(name: str) -> Path:
    return CONFIG_DIR / name


def load_yaml(name: str) -> dict:
    with config_path(name).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def data_path(key: str) -> Path:
    if key == "root_dir":
        return ML_ROOT
    try:
        return _DATA_DIRS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown data path key: {key}") from exc


def resolve_input_document(path: str | Path) -> Path:
    requested = Path(path).expanduser()
    candidates = [requested] if requested.is_absolute() else [Path.cwd() / requested, ML_ROOT / requested, REPO_ROOT / requested, SOURCE_DOCUMENTS_DIR / requested.name]
    tested = []
    for candidate in candidates:
        normalized = candidate.resolve(strict=False)
        tested.append(normalized)
        if normalized.is_file():
            return normalized
    tested_text = "\n".join(f"  - {candidate}" for candidate in tested)
    raise FileNotFoundError(
        f"Document introuvable: {path}\n"
        f"Répertoire courant: {Path.cwd()}\nML_ROOT: {ML_ROOT}\n"
        f"Dossier source_documents: {SOURCE_DOCUMENTS_DIR}\nChemins testés:\n{tested_text}"
    )


def resolve_input_directory(path: str | Path) -> Path:
    requested = Path(path).expanduser()
    candidates = [requested] if requested.is_absolute() else [Path.cwd() / requested, ML_ROOT / requested, REPO_ROOT / requested]
    tested = []
    for candidate in candidates:
        normalized = candidate.resolve(strict=False)
        tested.append(normalized)
        if normalized.is_dir():
            return normalized
    tested_text = "\n".join(f"  - {candidate}" for candidate in tested)
    raise FileNotFoundError(f"Dossier introuvable: {path}\nRépertoire courant: {Path.cwd()}\nML_ROOT: {ML_ROOT}\nChemins testés:\n{tested_text}")

