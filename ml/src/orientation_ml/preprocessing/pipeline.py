from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .feature_schema import FORBIDDEN_FEATURES, META_COLUMNS


def make_preprocessor(frame):
    features = [column for column in frame.columns if column not in META_COLUMNS]
    if FORBIDDEN_FEATURES.intersection(column.casefold() for column in features):
        raise ValueError("PII field cannot be used as an ML feature")
    numeric = frame[features].select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features if column not in numeric]
    transformers = []
    if numeric:
        transformers.append(("numeric", Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True)), ("scaler", StandardScaler())]), numeric))
    if categorical:
        transformers.append(("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), categorical))
    return ColumnTransformer(transformers, remainder="drop"), features

