import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
from importlib.util import find_spec
from pathlib import Path

from .paths import (
    ML_ROOT,
    MODELS_DIR,
    RAW_DIR,
    SOURCE_DOCUMENTS_DIR,
    VALIDATED_DIR,
    data_path,
    load_yaml,
    resolve_input_directory,
    resolve_input_document,
)


def doctor() -> int:
    print(f"Python: {platform.python_version()}")
    for package in ("pandas", "numpy", "scikit-learn", "joblib", "pydantic", "PyYAML", "PyMuPDF", "Pillow", "pytesseract", "rapidfuzz", "pillow-heif"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "ABSENT"
        print(f"{package}: {version}")
    from PIL import Image

    print("Formats documentaires supportés :")
    for label in ("PDF", "JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF"):
        print(f"  {label}: oui")
    print(f"  HEIC/HEIF: {'oui' if find_spec('pillow_heif') else 'non (installer pillow-heif)'}")
    print(f"  AVIF: {'oui' if '.avif' in Image.registered_extensions() else 'non (Pillow actuel)'}")
    binary = shutil.which("tesseract")
    fallback = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    binary = binary or (str(fallback) if fallback.exists() else None)
    print(f"Tesseract trouvé: {'oui' if binary else 'non'}")
    if binary:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = binary
            print(f"Tesseract: {pytesseract.get_tesseract_version()}")
            languages = pytesseract.get_languages(config="")
            print("Langues disponibles:")
            print("\n".join(languages))
            if "fra" not in languages:
                print("Langue française: NON INSTALLÉE")
                print("WARNING: fra.traineddata absent : l'OCR des relevés français fonctionnera moins bien.")
            else:
                print("Langue française: installée")
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            print(f"Tesseract erreur: {exc}")
    print(f"ML_ROOT: {ML_ROOT}")
    for key in ("documents_dir", "extracted_dir", "validated_dir", "raw_dir", "processed_dir", "splits_dir", "reference_dir"):
        path = data_path(key)
        print(f"{key}: {path}")
    labels = load_yaml("labels.yaml").get("target_fields", [])
    print("Labels configurés:", ", ".join(labels) or "[]")
    print("Documents:", sum(p.is_file() and p.name != ".gitkeep" for p in SOURCE_DOCUMENTS_DIR.iterdir()))
    print("Records validés:", len(list(VALIDATED_DIR.glob("*.json"))))
    print("Dataset disponible:", (RAW_DIR / "orientation_dataset.csv").exists())
    print("Modèle disponible:", (MODELS_DIR / "orientation_model.joblib").exists())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orientation-ml", description="Pipeline ML d'orientation universitaire")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("doctor")
    commands.add_parser("labels")
    extract = commands.add_parser("extract")
    extract.add_argument("document")
    extract.add_argument("--force", action="store_true", help="Réextraire même si le SHA256 existe déjà")
    extract_dir = commands.add_parser("extract-dir")
    extract_dir.add_argument("directory", nargs="?", default=str(SOURCE_DOCUMENTS_DIR))
    extract_dir.add_argument("--force", action="store_true", help="Réextraire aussi les documents déjà connus")
    review_parser = commands.add_parser("review")
    review_parser.add_argument("record_id")
    for name in ("build-dataset", "check-dataset", "split", "train", "evaluate"):
        commands.add_parser(name)
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("json_file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "labels":
            print(json.dumps(load_yaml("labels.yaml").get("target_fields", []), ensure_ascii=False, indent=2))
        elif args.command == "extract":
            from .ocr.extractor import extract as extract_document
            from .utils.hashing import sha256_file

            document = resolve_input_document(args.document)
            existing = None
            if not args.force:
                from .ocr.extractor import find_existing_record

                existing = find_existing_record(sha256_file(document))
            record = extract_document(document, force=args.force)
            if existing:
                print(f"Document déjà extrait : {record['record_id']}")
            print(json.dumps(record, ensure_ascii=False, indent=2))
        elif args.command == "extract-dir":
            from .ocr.document_reader import SUPPORTED
            from .ocr.extractor import extract as extract_document
            from .ocr.extractor import find_existing_record
            from .utils.hashing import sha256_file

            directory = resolve_input_directory(args.directory)
            documents = [item for item in sorted(directory.iterdir()) if item.is_file() and item.suffix.lower() in SUPPORTED]
            success = duplicates = failures = 0
            print(f"Documents trouvés : {len(documents)}")
            for document in documents:
                try:
                    existing = find_existing_record(sha256_file(document)) if not args.force else None
                    record = extract_document(document, force=args.force)
                    if existing:
                        duplicates += 1
                        print(f"Document déjà extrait : {record['record_id']} ({document.name})")
                    else:
                        success += 1
                        print(json.dumps(record, ensure_ascii=False))
                except (ValueError, RuntimeError) as exc:
                    failures += 1
                    print(f"Échec {document.name}: {exc}")
            print(f"Succès : {success} | Doublons : {duplicates} | Échecs : {failures}")
        elif args.command == "review":
            from .dataset.reviewer import review

            print(review(args.record_id))
        elif args.command == "build-dataset":
            from .dataset.builder import build_dataset

            print(f"Enregistrements construits: {len(build_dataset())}")
        elif args.command == "check-dataset":
            from .dataset.quality import check_dataset

            errors = check_dataset()
            print("Dataset valide" if not errors else "\n".join(errors))
            return int(bool(errors))
        elif args.command == "split":
            from .dataset.splitter import split_dataset

            print({key: len(value) for key, value in split_dataset().items()})
        elif args.command == "train":
            from .training.trainer import train

            print(train())
        elif args.command == "evaluate":
            from .evaluation.evaluator import evaluate

            print(json.dumps(evaluate(), indent=2))
        elif args.command == "predict":
            from .inference.predictor import predict

            print(json.dumps(predict(json.loads(args.json_file.read_text(encoding="utf-8"))), indent=2))
        else:
            parser.print_help()
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
