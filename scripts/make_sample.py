"""Gera a nota fiscal SINTÉTICA usada em exemplos/testes: samples/nota-sintetica-001.png.

Nenhum dado real de nota fiscal é utilizado (CLAUDE.md §9).
"""

from __future__ import annotations

from pathlib import Path

from tests.support import make_invoice_png


def main() -> None:
    target = Path("samples/nota-sintetica-001.png")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(make_invoice_png())
    print(f"amostra sintética gerada: {target}")


if __name__ == "__main__":
    main()
