class OCRNotAvailable(RuntimeError):
    """Tesseract OCR cannot be run in the current environment."""


class UnsupportedDocument(ValueError):
    """The input document format is unsupported."""


class UnreadableImage(ValueError):
    """The input is an image file that Pillow cannot decode."""


class NoScoresFound(ValueError):
    """No recognizable scores were found in extracted text."""


class InvalidTrainingRecord(ValueError):
    """A reviewed record does not meet the training schema."""


class UnknownFieldCode(ValueError):
    """A manually supplied field code is not configured."""


class DatasetTooSmall(ValueError):
    """There are not enough validated examples for this operation."""


class ClassTooSmall(ValueError):
    """At least one target class has too few training examples."""


class ModelNotTrained(RuntimeError):
    """No trained model artifact exists."""


class FeatureSchemaMismatch(RuntimeError):
    """Inference features are incompatible with the saved model."""
