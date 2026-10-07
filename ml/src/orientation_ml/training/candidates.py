from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ..preprocessing.pipeline import make_preprocessor


def candidate_models(train_frame):
    preprocessor, _ = make_preprocessor(train_frame)
    return {
        "logistic_regression": Pipeline([("preprocess", preprocessor), ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42))]),
        "random_forest": Pipeline([("preprocess", preprocessor), ("model", RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42))]),
    }

