import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..exceptions import OCRNotAvailable, UnreadableImage, UnsupportedDocument

SUPPORTED = {
    ".pdf", ".jpg", ".jpeg", ".jpe", ".png", ".webp", ".bmp", ".tif", ".tiff",
    ".gif", ".heic", ".heif", ".avif",
}
IMAGE_EXTENSIONS = SUPPORTED - {".pdf"}


@dataclass
class DocumentText:
    text: str
    pages: int
    ocr_used: bool
    ocr_engine: str | None = None
    warnings: list[str] = field(default_factory=list)


def _tesseract():
    import pytesseract

    binary = shutil.which("tesseract")
    fallback = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if not binary and fallback.exists():
        binary = str(fallback)
    if not binary:
        raise OCRNotAvailable("Tesseract introuvable. Installez Tesseract OCR puis ajoutez-le au PATH.")
    pytesseract.pytesseract.tesseract_cmd = binary
    return pytesseract


def _ocr(image, *, detect_orientation: bool = False):
    from .image_preprocessing import correct_orientation, deskew, prepare_image_for_ocr

    pytesseract = _tesseract()
    available = set(pytesseract.get_languages(config=""))
    lang = "fra+eng" if {"fra", "eng"}.issubset(available) else "eng" if "eng" in available else "fra" if "fra" in available else None
    if not lang:
        raise OCRNotAvailable("Tesseract est installé, mais aucun pack fra/eng n'est disponible.")
    warnings = []
    source = image
    if detect_orientation:
        source, warning = correct_orientation(image, pytesseract)
        if warning:
            warnings.append(warning)
    prepared = deskew(prepare_image_for_ocr(source))
    width, height = prepared.size
    if detect_orientation:
        import numpy as np

        gray = np.asarray(prepared.convert("L"))
        line_density = (gray[:, int(width * 0.05):int(width * 0.97)] < 110).mean(axis=1)
        active = [index for index in range(int(height * 0.28), int(height * 0.78)) if line_density[index] > 0.35]
        groups = []
        for index in active:
            if not groups or index - groups[-1][-1] > 2:
                groups.append([index])
            else:
                groups[-1].append(index)
        boundaries = [sum(group) / len(group) for group in groups]
        row_start = row_step = None
        for index in range(len(boundaries) - 1):
            gap = (boundaries[index + 1] - boundaries[index]) / height
            if 0.018 <= gap <= 0.05 and boundaries[index] / height < 0.48:
                steps = [
                    (boundaries[j + 1] - boundaries[j])
                    for j in range(index + 1, len(boundaries) - 1)
                    if 0.025 <= (boundaries[j + 1] - boundaries[j]) / height <= 0.05
                ]
                row_start = boundaries[index + 1]
                row_step = float(np.median(steps)) if steps else boundaries[index + 1] - boundaries[index]
                break
        if row_start is None or row_step is None:
            row_start, row_step = height * 0.39, height * 0.035
    else:
        row_start, row_step = height * 0.36, height * (0.31 / 9)
    table_lines = []
    if detect_orientation:
        import re

        from .score_parser import NUMBER, _number
        from .subject_normalizer import normalize_subject_prefix

    for row_index in range(9):
        row_padding = height * 0.006 if detect_orientation else 0
        y0 = int(row_start + row_index * row_step + row_padding)
        y1 = int(row_start + (row_index + 1) * row_step - row_padding)
        if y1 <= y0:
            continue
        left_margin, right_margin = (0.05, 0.97) if detect_orientation else (0.06, 0.96)
        row_image = prepared.crop((int(width * left_margin), y0, int(width * right_margin), y1))
        row_text = pytesseract.image_to_string(row_image, lang=lang, config="--psm 7").strip()
        if detect_orientation:
            row_osd = pytesseract.image_to_string(row_image, lang=lang, config="--psm 11")
            label_candidates = [
                pytesseract.image_to_string(
                    prepared.crop((int(width * 0.05), y0, int(width * 0.6), y1)), lang=lang, config="--psm 7"
                ),
                row_text,
                row_osd,
            ]
            label = None
            for candidate in label_candidates:
                match = NUMBER.search(candidate)
                candidate_label = candidate[:match.start()] if match else candidate
                candidate_label = re.sub(r"[|\[\]]", " ", candidate_label).strip()
                if normalize_subject_prefix(candidate_label):
                    label = candidate_label
                    break
            if label:
                optional = bool(re.search(r"\b(?:boni|facultative|optionnelle?)\b", label, re.IGNORECASE))

                def read_cell(left, right, psm, top=y0, bottom=y1):
                    crop = prepared.crop((int(width * left), top, int(width * right), bottom))
                    return pytesseract.image_to_string(crop, lang=lang, config=f"--psm {psm}").strip()

                coefficient_text = read_cell(0.60, 0.74, 11)
                raw_text = read_cell(0.64, 0.76, 7)
                max_text = read_cell(0.76, 0.90, 7)
                coefficient = None
                if not optional:
                    for candidate in (coefficient_text, row_text, row_osd):
                        values = [_number(value) for value in NUMBER.findall(candidate)]
                        if values and values[0].is_integer() and 1 <= values[0] <= 5:
                            coefficient = values[0]
                            break
                raw_values = NUMBER.findall(raw_text)
                max_values = NUMBER.findall(max_text)
                coefficient_part = "" if optional or coefficient is None else str(int(coefficient))
                raw_part = raw_values[0] if raw_values else ""
                max_part = max_values[0] if max_values else ""
                row_text = " ".join(part for part in (label, coefficient_part, raw_part, max_part) if part)
            else:
                row_text = ""
        if row_text:
            table_lines.append(" ".join(row_text.split()))
    table_end = min(height, int(row_start + 9 * row_step))
    header = prepared.crop((0, 0, width, int(height * 0.34)))
    header_text = pytesseract.image_to_string(header, lang=lang, config="--psm 6")
    summary = prepared.crop((int(width * 0.55), int(height * 0.68), int(width * 0.98), int(height * 0.78)))
    summary_text = pytesseract.image_to_string(summary, lang=lang, config="--psm 6")
    summary_text += "\n" + pytesseract.image_to_string(summary, lang=lang, config="--psm 11")
    average_y = min(height, int(table_end + height * 0.04))
    average_cell = prepared.crop((int(width * 0.68), average_y, int(width * 0.9), min(height, average_y + int(height * 0.025))))
    average_text = pytesseract.image_to_string(average_cell, lang=lang, config="--psm 7")
    table_header = "Matières Coef Note Note Max" if detect_orientation else ""
    return header_text + "\n" + table_header + "\n" + "\n".join(table_lines) + "\n" + summary_text + "\nMoyenne " + average_text, lang, warnings


def _is_pdf(path: Path) -> bool:
    if path.suffix.lower() == ".pdf":
        return True
    try:
        with path.open("rb") as stream:
            return stream.read(5) == b"%PDF-"
    except OSError:
        return False


def _read_pdf(path: Path) -> DocumentText:
    import pymupdf
    from PIL import Image

    try:
        doc = pymupdf.open(path)
        pages, used, engine, warnings = [], False, None, []
        for page in doc:
            text = page.get_text("text").strip()
            if len(text) < 30:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(4, 4), alpha=False)
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                text, engine, page_warnings = _ocr(image)
                warnings.extend(page_warnings)
                used = True
            pages.append(text)
        if used and engine == "eng":
            warnings.append("fra.traineddata absent; OCR effectué avec eng. Installez la langue fra pour améliorer les relevés français.")
        return DocumentText("\n\n".join(pages), len(pages), used, engine, warnings)
    except OCRNotAvailable:
        raise
    except Exception as exc:
        raise UnsupportedDocument(f"PDF illisible ou corrompu : {path.name}") from exc


def _register_heif(path: Path) -> None:
    if path.suffix.lower() not in {".heic", ".heif"}:
        return
    try:
        from pillow_heif import register_heif_opener
    except ImportError as exc:
        raise UnsupportedDocument("Support HEIC/HEIF indisponible. Installez pillow-heif.") from exc
    register_heif_opener()


def _read_image(path: Path) -> DocumentText:
    from PIL import Image, ImageSequence, UnidentifiedImageError

    _register_heif(path)
    try:
        with Image.open(path) as image:
            image_format = (image.format or "").upper()
            frame_count = getattr(image, "n_frames", 1)
            warnings = []
            if image_format in {"GIF", "WEBP"} and frame_count > 1:
                warnings.append("Image animée/multi-frame détectée; première frame utilisée.")
            if image_format in {"TIFF", "TIF"}:
                frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
            else:
                frames = [image.copy()]
    except UnsupportedDocument:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        if path.suffix.lower() == ".avif" and ".avif" not in Image.registered_extensions():
            raise UnsupportedDocument("Format AVIF non supporté par l'installation Pillow actuelle.") from exc
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise UnsupportedDocument(f"Format non supporté : {path.suffix or '(sans extension)'}") from exc
        raise UnreadableImage(f"Image illisible ou corrompue : {path.name}") from exc

    texts, engines = [], []
    for frame in frames:
        text, engine, frame_warnings = _ocr(frame, detect_orientation=True)
        texts.append(text)
        engines.append(engine)
        warnings.extend(frame_warnings)
    if engines and all(engine == "eng" for engine in engines):
        warnings.append("fra.traineddata absent; OCR effectué avec eng. Installez la langue fra pour améliorer les relevés français.")
    return DocumentText("\n\n".join(texts), len(frames), True, "+".join(sorted(set(engines))) if engines else None, warnings)


def read_document(path: Path) -> DocumentText:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if _is_pdf(path):
        return _read_pdf(path)
    return _read_image(path)
