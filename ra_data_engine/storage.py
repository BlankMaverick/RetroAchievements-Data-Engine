"""Local persistence helpers for collected API responses."""

import json
from pathlib import Path


def save_json(data: object, output_path: str | Path) -> None:
    """Write data as readable UTF-8 JSON."""
    with Path(output_path).open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")
