from orientation_ml.dataset.builder import PII_KEYS


def test_pii_fields_are_explicitly_forbidden():
    assert {"email", "matricule", "student_name"}.issubset(PII_KEYS)

