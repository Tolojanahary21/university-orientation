from orientation_ml.evaluation.metrics import classification_metrics


class FakeModel:
    def __init__(self):
        self.classes_ = ["A", "B"]

    def predict(self, features):
        return ["A", "B"]

    def predict_proba(self, features):
        return [[0.8, 0.2], [0.1, 0.9]]


def test_metrics_include_top_k():
    metrics = classification_metrics(FakeModel(), [[], []], ["A", "B"], top_k=1)
    assert metrics["accuracy"] == 1
    assert metrics["top_k_accuracy"] == 1

