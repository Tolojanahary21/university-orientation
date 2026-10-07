import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def prepare_image_for_ocr(image: Image.Image) -> Image.Image:
    """Return a gently enhanced, EXIF-corrected RGB copy with transparency on white."""
    result = ImageOps.exif_transpose(image.copy())
    if result.mode in {"RGBA", "LA"} or "transparency" in result.info:
        rgba = result.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        result = Image.alpha_composite(background, rgba).convert("RGB")
    else:
        result = result.convert("RGB")
    if result.width < 1200 or result.height < 1200:
        scale = min(2.0, 1200 / min(result.size))
        result = result.resize((round(result.width * scale), round(result.height * scale)), Image.Resampling.LANCZOS)
    result = ImageOps.autocontrast(result.convert("L")).convert("RGB")
    return ImageEnhance.Sharpness(ImageEnhance.Contrast(result).enhance(1.08)).enhance(1.1)


def prepare_image(image: Image.Image) -> Image.Image:
    """Backward-compatible alias."""
    return prepare_image_for_ocr(image)


def correct_orientation(image: Image.Image, pytesseract) -> tuple[Image.Image, str | None]:
    """Try Tesseract OSD; retain EXIF-corrected pixels if OSD is inconclusive."""
    import re

    result = ImageOps.exif_transpose(image.copy())
    try:
        orientation = pytesseract.image_to_osd(result)
        match = re.search(r"Rotate:\s*(\d+)", orientation)
        rotation = int(match.group(1)) if match else 0
        confidence_match = re.search(r"Orientation confidence:\s*([\d.]+)", orientation)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        if confidence < 5:
            return result, "Orientation automatique incertaine; orientation EXIF conservée."
        if rotation in {90, 180, 270}:
            result = result.rotate(-rotation, expand=True, fillcolor="white")
        return result, None
    except (OSError, RuntimeError, ValueError):
        return result, "Orientation automatique incertaine; orientation EXIF conservée."


def deskew(image: Image.Image) -> Image.Image:
    """Correct small scan rotations using horizontal projection, with Pillow only."""
    gray = np.asarray(image.convert("L"))
    if gray.shape[0] > 1400:
        step = max(1, gray.shape[0] // 1400)
        gray = gray[::step, ::step]
    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-4.0, 4.01, 0.25):
        rotated = Image.fromarray(gray).rotate(float(angle), resample=Image.Resampling.BILINEAR, expand=False, fillcolor=255)
        ink = 255 - np.asarray(rotated)
        projection = ink.sum(axis=1)
        score = float(np.var(projection))
        if score > best_score:
            best_angle, best_score = float(angle), score
    if abs(best_angle) < 0.25:
        return image
    return image.rotate(best_angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
