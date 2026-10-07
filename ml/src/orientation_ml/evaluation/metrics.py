import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    top_k_accuracy_score,
)


def classification_metrics(model, features, target, labels=None, top_k: int = 3) -> dict:
    predicted = model.predict(features)
    result = {"accuracy": float(accuracy_score(target, predicted)), "precision_macro": float(precision_score(target, predicted, average="macro", zero_division=0)), "recall_macro": float(recall_score(target, predicted, average="macro", zero_division=0)), "f1_macro": float(f1_score(target, predicted, average="macro", zero_division=0))}
    if hasattr(model, "predict_proba"):
        probabilities = np.asarray(model.predict_proba(features))
        ordered_labels = labels or model.classes_
        if len(ordered_labels) == 2:
            top = probabilities.argmax(axis=1)
            predicted_labels = [ordered_labels[index] for index in top]
            result["top_k_accuracy"] = float(accuracy_score(target, predicted_labels))
        else:
            result["top_k_accuracy"] = float(top_k_accuracy_score(target, probabilities, k=min(top_k, len(ordered_labels)), labels=ordered_labels))
    return result

