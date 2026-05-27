"""Exportação de cenários simulados."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone


def exportar_csv(registros: list[dict]) -> bytes:
    if not registros:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=registros[0].keys())
    writer.writeheader()
    writer.writerows(registros)
    return buf.getvalue().encode("utf-8-sig")


def exportar_json(registros: list[dict], meta: dict | None = None) -> bytes:
    payload = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
        "cenarios": registros,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
