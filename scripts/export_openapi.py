"""Exporta o schema OpenAPI da API para docs/openapi.json."""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    target = Path("docs/openapi.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OpenAPI exportado para {target}")


if __name__ == "__main__":
    main()
