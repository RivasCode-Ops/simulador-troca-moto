"""Utilitários de formatação para a interface."""

from __future__ import annotations


def brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor: float) -> str:
    return f"{valor:.2f}%"
