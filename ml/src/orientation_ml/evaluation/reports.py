import json
from pathlib import Path


def write_model_card(metadata: dict, metrics: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("# Model card\n\nThis model was trained only from human validated records.\n\n## Metadata\n\n```json\n" + json.dumps(metadata, indent=2) + "\n```\n\n## Test metrics\n\n```json\n" + json.dumps(metrics, indent=2) + "\n```\n", encoding="utf-8")

