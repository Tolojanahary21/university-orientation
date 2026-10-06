from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATASET = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "student_scores.csv"
)

PROCESSED_DATASET = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "student_scores_processed.csv"
)


TARGET = "career_aspiration"

COLUMNS_TO_DROP = [
    "id",
    "first_name",
    "last_name",
    "email",
    "gender",
]


def main() -> None:
    print("=" * 70)
    print("PREPROCESSING DATASET")
    print("=" * 70)

    if not RAW_DATASET.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {RAW_DATASET}"
        )

    # 1. Charger le dataset brut
    df = pd.read_csv(RAW_DATASET)

    print(f"Lignes initiales : {len(df)}")
    print(f"Colonnes initiales : {len(df.columns)}")

    # 2. Vérifier la cible
    if TARGET not in df.columns:
        raise ValueError(
            f"Colonne cible absente : {TARGET}"
        )

    # 3. Supprimer les informations personnelles
    existing_columns_to_drop = [
        column
        for column in COLUMNS_TO_DROP
        if column in df.columns
    ]

    df = df.drop(
        columns=existing_columns_to_drop
    )

    # 4. Supprimer les lignes dont la cible est Unknown
    unknown_count = (
        df[TARGET]
        .astype(str)
        .str.strip()
        .eq("Unknown")
        .sum()
    )

    print(
        f"Lignes avec career_aspiration=Unknown : "
        f"{unknown_count}"
    )

    df = df[
        ~df[TARGET]
        .astype(str)
        .str.strip()
        .eq("Unknown")
    ].copy()

    # 5. Supprimer d'éventuels doublons
    duplicate_count = df.duplicated().sum()

    print(
        f"Doublons détectés après nettoyage : "
        f"{duplicate_count}"
    )

    if duplicate_count:
        df = df.drop_duplicates()

    # 6. Vérifier les valeurs manquantes
    missing_count = int(
        df.isna().sum().sum()
    )

    print(
        f"Valeurs manquantes restantes : "
        f"{missing_count}"
    )

    # 7. Réinitialiser l'index
    df = df.reset_index(drop=True)

    # 8. Créer le dossier processed si nécessaire
    PROCESSED_DATASET.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 9. Sauvegarder
    df.to_csv(
        PROCESSED_DATASET,
        index=False,
    )

    print("\n" + "=" * 70)
    print("RESULTAT")
    print("=" * 70)

    print(f"Lignes finales : {len(df)}")
    print(f"Colonnes finales : {len(df.columns)}")

    print("\nColonnes conservées :")

    for column in df.columns:
        print(f"- {column}")

    print("\nClasses de la cible :")
    print(
        df[TARGET]
        .value_counts()
        .to_string()
    )

    print(
        "\nNombre de classes :",
        df[TARGET].nunique(),
    )

    print(
        f"\nDataset généré : "
        f"{PROCESSED_DATASET}"
    )


if __name__ == "__main__":
    main()