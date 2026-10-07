from pathlib import Path

import pytest
from PIL import Image

from orientation_ml.exceptions import UnreadableImage, UnsupportedDocument
from orientation_ml.ocr import document_reader
from orientation_ml.ocr.image_preprocessing import correct_orientation, prepare_image_for_ocr

FIXTURES = Path(__file__).parent / "fixtures" / "document_images"


@pytest.fixture(autouse=True)
def fake_ocr(monkeypatch):
    monkeypatch.setattr(document_reader, "_ocr", lambda image, **kwargs: ("fixture OCR", "fra+eng", []))


@pytest.mark.parametrize("filename", ["sample.jpg", "sample.jpeg", "sample.png", "sample.webp", "sample.bmp"])
def test_common_raster_formats_are_opened_by_pillow(filename):
    result = document_reader.read_document(FIXTURES / filename)
    assert result.text == "fixture OCR"
    assert result.pages == 1
    assert result.ocr_used is True


def test_extension_is_not_the_only_format_check():
    path = FIXTURES / "unknown.xyz"
    assert document_reader.read_document(path).pages == 1


def test_tiff_multipage_ocr_processes_every_frame(monkeypatch):
    calls = []
    monkeypatch.setattr(document_reader, "_ocr", lambda image, **kwargs: (calls.append(image.size) or f"frame {len(calls)}", "fra+eng", []))
    result = document_reader.read_document(FIXTURES / "multipage.tiff")
    assert result.pages == 2
    assert result.text == "frame 1\n\nframe 2"
    assert len(calls) == 2


def test_animated_gif_uses_first_frame_and_warns():
    result = document_reader.read_document(FIXTURES / "animated.gif")
    assert result.pages == 1
    assert any("frame utilisée" in warning for warning in result.warnings)


def test_transparent_images_are_flattened_on_white():
    with Image.open(FIXTURES / "transparent.png") as source:
        prepared = prepare_image_for_ocr(source)
    assert prepared.mode == "RGB"
    assert prepared.getpixel((0, 0)) == (255, 255, 255)


def test_exif_orientation_is_applied_without_mutating_source():
    with Image.open(FIXTURES / "exif_orientation.jpg") as source:
        before = source.size
        prepared = prepare_image_for_ocr(source)
        assert source.size == before
    assert prepared.width > prepared.height


def test_osd_failure_keeps_exif_corrected_image_and_returns_warning():
    class FailedOSD:
        @staticmethod
        def image_to_osd(_image):
            raise RuntimeError("OSD unavailable")

    with Image.open(FIXTURES / "exif_orientation.jpg") as source:
        oriented, warning = correct_orientation(source, FailedOSD)
    assert oriented.width > oriented.height
    assert warning is not None


def test_corrupt_image_and_unknown_extension_have_clear_errors():
    with pytest.raises(UnreadableImage, match="Image illisible ou corrompue"):
        document_reader.read_document(FIXTURES / "corrupt.jpg")
    with pytest.raises(UnsupportedDocument, match="Format non support"):
        document_reader.read_document(FIXTURES / "invalid.xyz")


def test_heic_support_is_optional_and_reports_missing_dependency(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "pillow_heif", None)
    with pytest.raises(UnsupportedDocument, match="Installez pillow-heif"):
        document_reader.read_document(FIXTURES / "fake_phone.heic")


def test_heic_when_pillow_heif_is_installed():
    if __import__("importlib.util").util.find_spec("pillow_heif") is None:
        pytest.skip("pillow-heif unavailable")
    result = document_reader.read_document(FIXTURES / "sample.heic")
    assert result.pages == 1


def test_avif_if_pillow_has_a_decoder():
    if ".avif" not in Image.registered_extensions():
        pytest.skip("Pillow AVIF plugin unavailable")
    path = FIXTURES / "sample.avif"
    if not path.exists():
        pytest.skip("Pillow AVIF encoder unavailable")
    assert document_reader.read_document(path).pages == 1
