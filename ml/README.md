# Orientation ML

Pipeline local d'extraction des notes scolaires, de validation humaine et de préparation à l'entraînement. Le package Python est `orientation_ml`, installé depuis `src/`. Aucun entraînement final n'est lancé sans données réelles validées et aucun code de filière n'est inventé.

## Installation (Windows PowerShell)

Depuis `D:\Projets\Machine Learning\ml` :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Installez Tesseract OCR séparément. Le code privilégie les langues `fra+eng`, puis continue avec `eng` si le pack français est absent. `doctor` affiche un avertissement dans ce cas. Pillow traite les images; `pillow-heif` active HEIC/HEIF et Pillow 12 de l'environnement courant prend en charge AVIF.

## Utilisation

```powershell
python -m orientation_ml.cli doctor
```

Déposez les relevés dans `data\source_documents\`. Puis lancez :

```powershell
python -m orientation_ml.cli extract "releve.pdf"
python -m orientation_ml.cli extract "data\source_documents\releve.pdf"
python -m orientation_ml.cli extract "releve_telephone.jpg"
python -m orientation_ml.cli extract "releve.png"
python -m orientation_ml.cli extract "releve.heic"
python -m orientation_ml.cli extract "releve.pdf" --force
python -m orientation_ml.cli extract-dir
python -m orientation_ml.cli review RECORD_ID
```

`extract` accepte PDF, JPG/JPEG/JPE, PNG, WEBP, BMP, TIF/TIFF, GIF, HEIC/HEIF et AVIF lorsque le décodeur correspondant est disponible. TIFF multipage est lu page par page; GIF animé utilise sa première frame. Une extraction identique (même SHA-256) réutilise son JSON; `--force` déclenche une nouvelle extraction sans supprimer les enregistrements validés. `extract-dir` parcourt tous les formats reconnus dans `data/source_documents/` et affiche un bilan succès/doublons/échecs.

Une extraction écrit le JSON structuré et le texte OCR dans `data/extracted/`. Les champs d'identité ne sont pas recopiés dans le JSON structuré ni dans le dataset; le texte brut demeure une donnée sensible locale.

Ajoutez à `config/labels.yaml` uniquement des codes vérifiés dans `backend/fields.code`. La commande `review` demande une validation humaine et refuse les codes non configurés.

```powershell
python -m orientation_ml.cli labels
python -m orientation_ml.cli build-dataset
python -m orientation_ml.cli check-dataset
python -m orientation_ml.cli split
python -m orientation_ml.cli train
python -m orientation_ml.cli evaluate
python -m orientation_ml.cli predict profile.json
```

`train` requiert au moins 10 exemples d'entraînement par classe (seuil configurable dans `config/training.yaml`) et avertit sous 20. Le prétraitement est appris dans le pipeline sur train seulement. Aucun faux dataset ni modèle n'est créé. DVC n'est pas configuré ou initialisé; MLflow n'est pas exécuté.

## Tests et qualité

```powershell
python -m pytest tests -q
python -m ruff check .
```

Les documents, extractions, données validées, datasets, splits, modèles et caches sont ignorés par Git. Ne placez aucune donnée d'identité dans les features.
