from pathlib import Path

from orientation_ml.ocr.extractor import _extract_average, _extract_mention, _extract_series, extract_graduation_year


def test_graduation_year_uses_exam_label_not_birth_year():
    text = "Né le 23 septembre 2005\nBaccalauréat\nAnnée 2023"
    assert extract_graduation_year(text) == 2023


def test_birth_year_is_not_used_as_graduation_year():
    assert extract_graduation_year("Né le 23 septembre 2005") is None


def test_extracts_series_average_and_mention_from_bac_fixture():
    text = "Option D\nMoyenne : 11,59\nMention : Assez Bien"
    assert _extract_series(text) == "D"
    assert _extract_average(text) == 11.59
    assert _extract_mention(text) == "Assez Bien"


def test_identical_source_is_deduplicated_and_force_keeps_validated_data(monkeypatch, tmp_path):
    import json

    from orientation_ml.ocr import extractor
    from orientation_ml.ocr.document_reader import DocumentText

    extracted = tmp_path / "extracted"
    validated = tmp_path / "validated"
    extracted.mkdir()
    validated.mkdir()
    protected = validated / "keep.json"
    protected.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(extractor, "data_path", lambda key: extracted if key == "extracted_dir" else validated)
    calls = []

    def fake_read_document(_path):
        calls.append(1)
        return DocumentText("Mathematics 10", 1, True, "fra+eng")

    monkeypatch.setattr(extractor, "read_document", fake_read_document)
    source = Path(__file__).parent / "fixtures" / "document_images" / "sample.bmp"
    first = extractor.extract(source)
    second = extractor.extract(source)
    assert first["record_id"] == second["record_id"]
    assert first["source_sha256"] == second["source_sha256"]
    assert len(calls) == 1
    forced = extractor.extract(source, force=True)
    assert forced["record_id"] != first["record_id"]
    assert len(calls) == 2
    assert protected.read_text(encoding="utf-8") == "{}"
    assert json.loads((extracted / f"{first['record_id']}.json").read_text(encoding="utf-8"))["source_sha256"] == first["source_sha256"]
