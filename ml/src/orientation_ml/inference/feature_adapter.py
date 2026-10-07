import pandas as pd

from ..dataset.builder import SUBJECTS


def to_frame(payload: dict) -> pd.DataFrame:
    scores = payload.get("scores", {})
    row = {"bac_series": payload.get("bac_series"), "graduation_year": payload.get("graduation_year"), "average_score": payload.get("average_score"), "mention": payload.get("mention")}
    row.update({f"score_{subject}": (scores.get(subject) or {}).get("normalized_score", (scores.get(subject) or {}).get("value")) if isinstance(scores.get(subject), dict) else scores.get(subject) for subject in SUBJECTS})
    return pd.DataFrame([row])

