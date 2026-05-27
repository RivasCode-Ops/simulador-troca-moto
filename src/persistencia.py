"""Persistência de simulações em disco (JSON local)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

ARQUIVO = Path(__file__).resolve().parent.parent / "data" / "simulacoes.json"
MAX_REGISTROS = 100
VERSAO = 1


def _store_vazio() -> dict[str, Any]:
    return {"versao": VERSAO, "simulacoes": []}


def _ler_arquivo() -> dict[str, Any]:
    if not ARQUIVO.exists():
        return _store_vazio()
    try:
        data = json.loads(ARQUIVO.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "simulacoes" not in data:
            return _store_vazio()
        return data
    except (json.JSONDecodeError, OSError):
        return _store_vazio()


def _gravar(store: dict[str, Any]) -> None:
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def carregar() -> list[dict]:
    """Lista mais recente primeiro."""
    return list(_ler_arquivo().get("simulacoes", []))


def salvar(snapshot: dict) -> dict:
    store = _ler_arquivo()
    registro = dict(snapshot)
    registro.setdefault("id", str(uuid.uuid4()))
    if "salvo_em_iso" not in registro:
        agora = datetime.now()
        registro["salvo_em_iso"] = agora.isoformat(timespec="seconds")
        registro["salvo_em"] = agora.strftime("%d/%m %H:%M")
    sims = [registro, *store.get("simulacoes", [])]
    store["simulacoes"] = sims[:MAX_REGISTROS]
    store["versao"] = VERSAO
    _gravar(store)
    return registro


def excluir(registro_id: str) -> bool:
    store = _ler_arquivo()
    antes = len(store.get("simulacoes", []))
    store["simulacoes"] = [s for s in store.get("simulacoes", []) if s.get("id") != registro_id]
    if len(store["simulacoes"]) == antes:
        return False
    _gravar(store)
    return True


def limpar_todos() -> None:
    _gravar(_store_vazio())
