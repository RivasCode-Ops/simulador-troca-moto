"""Pendências de widgets Streamlit (aplicar antes de instanciar inputs)."""

from __future__ import annotations

SNAPSHOT_PENDENTE_KEY = "_snapshot_pendente"
PENDING_VALOR_USADA_KEY = "_pending_valor_usada"


def aplicar_pendentes_sidebar() -> None:
    """Aplica valores pendentes antes dos st.number_input da sidebar."""
    import streamlit as st

    from .historico import aplicar_snapshot_na_sessao

    if snap := st.session_state.pop(SNAPSHOT_PENDENTE_KEY, None):
        aplicar_snapshot_na_sessao(snap)
    if valor := st.session_state.pop(PENDING_VALOR_USADA_KEY, None):
        st.session_state["valor_usada"] = float(valor)
