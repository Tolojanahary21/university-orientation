from pathlib import Path

import pytest

from orientation_ml.paths import ML_ROOT, SOURCE_DOCUMENTS_DIR, resolve_input_document


def test_canonical_ml_root_and_document_dir():
    assert ML_ROOT.name == "ml"
    assert SOURCE_DOCUMENTS_DIR == ML_ROOT / "data" / "source_documents"


def test_resolve_absolute_path(tmp_path):
    file = tmp_path / "sample.pdf"
    file.write_bytes(b"test")
    assert resolve_input_document(file) == file.resolve()


def test_resolve_relative_path_from_ml_root(monkeypatch, tmp_path):
    monkeypatch.chdir(ML_ROOT.parent)
    relative = Path(ML_ROOT.name) / "data" / "source_documents" / "test-paths-fixture.tmp"
    expected = SOURCE_DOCUMENTS_DIR / relative.name
    expected.write_text("fixture", encoding="utf-8")
    try:
        assert resolve_input_document(relative) == expected.resolve()
    finally:
        expected.unlink()


def test_resolve_filename_only(tmp_path, monkeypatch):
    monkeypatch.setattr("orientation_ml.paths.SOURCE_DOCUMENTS_DIR", tmp_path)
    file = tmp_path / "sample.pdf"
    file.write_bytes(b"test")
    assert resolve_input_document("sample.pdf") == file.resolve()


def test_invalid_path_is_helpful():
    with pytest.raises(FileNotFoundError, match="Chemins testés") as error:
        resolve_input_document("definitely-not-a-real-document.pdf")
    assert str(ML_ROOT) in str(error.value)

