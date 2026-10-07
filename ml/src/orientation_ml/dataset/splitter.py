import pandas as pd
from sklearn.model_selection import train_test_split

from ..paths import data_path, load_yaml


class DatasetTooSmall(ValueError):
    pass


def split_dataset(frame: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    if frame is None:
        frame = pd.read_csv(data_path("raw_dir") / "orientation_dataset.csv")
    target = load_yaml("data.yaml")["target_column"]
    cfg = load_yaml("training.yaml")
    counts = frame[target].value_counts()
    if counts.min() < 3:
        raise DatasetTooSmall("Au moins 3 exemples par classe sont requis pour créer les splits stratifiés.")
    train, remaining = train_test_split(frame, test_size=cfg["test_size"] + cfg["validation_size"], random_state=cfg["random_state"], stratify=frame[target])
    relative_val = cfg["validation_size"] / (cfg["test_size"] + cfg["validation_size"])
    valid, test = train_test_split(remaining, test_size=1-relative_val, random_state=cfg["random_state"], stratify=remaining[target])
    output = data_path("splits_dir")
    output.mkdir(parents=True, exist_ok=True)
    result = {"train": train, "validation": valid, "test": test}
    for name, subset in result.items():
        subset.to_csv(output / f"{name}.csv", index=False)
    return result

