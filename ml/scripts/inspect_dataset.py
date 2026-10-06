from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "student_scores.csv"
)


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    print("=" * 70)
    print("DATASET")
    print("=" * 70)

    print(f"Fichier : {DATASET_PATH}")
    print(f"Nombre de lignes : {len(df)}")
    print(f"Nombre de colonnes : {len(df.columns)}")

    print("\nCOLONNES")
    print("-" * 70)

    for column in df.columns:
        print(column)

    print("\nTYPES")
    print("-" * 70)
    print(df.dtypes)

    print("\nVALEURS MANQUANTES")
    print("-" * 70)

    missing = df.isna().sum()
    print(missing[missing > 0])

    print("\nDOUBLONS")
    print("-" * 70)
    print(df.duplicated().sum())

    print("\nAPERÇU")
    print("-" * 70)
    print(df.head())

    target = "career_aspiration"

    if target in df.columns:
        print("\nTARGET : career_aspiration")
        print("-" * 70)

        print(
            df[target]
            .value_counts(dropna=False)
            .to_string()
        )

        print(
            "\nNombre de classes :",
            df[target].nunique()
        )
    else:
        print(
            "\nATTENTION : la colonne "
            "'career_aspiration' n'existe pas."
        )

        print(
            "Nous devrons identifier la vraie "
            "colonne cible avant de continuer."
        )


if __name__ == "__main__":
    main()