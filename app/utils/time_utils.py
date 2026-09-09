from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """Timestamp UTC em ISO 8601, sem microssegundos, sufixo `Z`."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
