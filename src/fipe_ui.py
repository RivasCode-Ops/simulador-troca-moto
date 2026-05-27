"""Interface Streamlit — consulta FIPE online."""

from __future__ import annotations

import streamlit as st

from .fipe import FipeApiError, consultar_preco, listar_anos, listar_marcas, listar_modelos
from .sessao_ui import PENDING_VALOR_USADA_KEY
from .fipe_analise import analisar_fipe_vs_venda
from .ui import brl, pct

SESSION_FIPE = "fipe_ultima_consulta"


@st.cache_data(ttl=3600, show_spinner=False)
def _marcas_cached() -> list[tuple[str, str]]:
    return [(m.codigo, m.nome) for m in listar_marcas()]


@st.cache_data(ttl=3600, show_spinner=False)
def _modelos_cached(codigo_marca: str) -> list[tuple[str, str]]:
    return [(m.codigo, m.nome) for m in listar_modelos(codigo_marca)]


@st.cache_data(ttl=3600, show_spinner=False)
def _anos_cached(codigo_marca: str, codigo_modelo: str) -> list[tuple[str, str]]:
    return [(a.codigo, a.nome) for a in listar_anos(codigo_marca, codigo_modelo)]


def render_consulta_fipe(preco_venda: float, custo_extra: float) -> None:
    """Bloco Consulta FIPE — tipo fixo moto."""
    with st.expander("🏷️ Consulta FIPE online", expanded=False):
        st.caption(
            "Preço médio de mercado (tabela FIPE via [API Parallelum](https://deividfortuna.github.io/fipe/)). "
            "Referência para validar seu preço de venda da usada."
        )

        try:
            marcas = _marcas_cached()
        except FipeApiError as e:
            st.error(str(e))
            return

        if not marcas:
            st.warning("Nenhuma marca retornada pela API.")
            return

        mapa_marcas = {nome: cod for cod, nome in marcas}
        nomes_marcas = [nome for _, nome in marcas]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("Tipo", value="Moto", disabled=True)
            marca_nome = st.selectbox("Marca", nomes_marcas, key="fipe_marca")
        cod_marca = mapa_marcas[marca_nome]

        try:
            modelos = _modelos_cached(cod_marca)
        except FipeApiError as e:
            st.error(str(e))
            return

        if not modelos:
            st.warning("Nenhum modelo para esta marca.")
            return

        mapa_modelos = {nome: cod for cod, nome in modelos}
        nomes_modelos = [nome for _, nome in modelos]

        with c2:
            modelo_nome = st.selectbox("Modelo", nomes_modelos, key="fipe_modelo")
        cod_modelo = mapa_modelos[modelo_nome]

        try:
            anos = _anos_cached(cod_marca, cod_modelo)
        except FipeApiError as e:
            st.error(str(e))
            return

        if not anos:
            st.warning("Nenhum ano/modelo disponível.")
            return

        mapa_anos = {nome: cod for cod, nome in anos}
        nomes_anos = [nome for _, nome in anos]

        with c3:
            ano_nome = st.selectbox("Ano / modelo", nomes_anos, key="fipe_ano")
        cod_ano = mapa_anos[ano_nome]

        st.caption(f"Seu preço de venda (moto usada): **{brl(preco_venda)}**")

        if st.button("Buscar FIPE", type="primary", key="fipe_buscar"):
            with st.spinner("Consultando tabela FIPE…"):
                try:
                    preco = consultar_preco(cod_marca, cod_modelo, cod_ano)
                    analise = analisar_fipe_vs_venda(preco, preco_venda, custo_extra)
                    st.session_state[SESSION_FIPE] = analise
                except FipeApiError as e:
                    st.error(str(e))

        if SESSION_FIPE not in st.session_state:
            return

        a = st.session_state[SESSION_FIPE]

        st.markdown("#### Resultado")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Preço FIPE", brl(a.preco_fipe))
        m2.metric("Seu preço alvo", brl(a.preco_venda))
        m3.metric("Diferença", brl(a.diferenca_reais), delta=a.rotulo_diferenca)
        if a.cobertura_custo_extra_pct is not None:
            m4.metric(
                "Cobre custo extra",
                f"{a.cobertura_custo_extra_pct:.0f}%",
                help="Quanto o valor acima da FIPE cobre do custo extra da troca",
            )
        else:
            m4.metric("Cobre custo extra", "—")

        st.markdown(
            f"**{a.marca} · {a.modelo}** · ref. {a.mes_referencia} · "
            f"código FIPE `{a.codigo_fipe}` · {a.combustivel}"
        )

        if a.diferenca_reais > 0:
            st.success(
                f"Você pede **{brl(a.diferenca_reais)}** ({pct(a.diferenca_pct)}) acima da FIPE."
            )
            if a.cobertura_custo_extra_pct is not None and custo_extra > 0:
                if a.cobertura_custo_extra_pct >= 100:
                    st.info(
                        f"O sobrepreço cobre **100%** do custo extra ({brl(custo_extra)})."
                    )
                else:
                    st.warning(
                        f"O sobrepreço cobre **{a.cobertura_custo_extra_pct:.0f}%** do custo extra. "
                        f"Mesmo acima da FIPE, ainda faltam **{brl(a.perda_apos_fipe or 0)}** para compensar juros e risco."
                    )
        elif a.diferenca_reais < 0:
            st.error(
                f"Você pede **{brl(abs(a.diferenca_reais))}** abaixo da FIPE "
                f"({abs(a.diferenca_pct):.1f}%) — negociação mais difícil."
            )
            if custo_extra > 0:
                st.caption(
                    f"Custo extra da troca: **{brl(custo_extra)}** — vender abaixo da FIPE não gera folga para cobrir."
                )
        else:
            st.info("Preço alvo igual à FIPE — referência neutra de mercado.")

        if st.button("Usar valor FIPE como moto usada (R$)", key="fipe_aplicar"):
            st.session_state[PENDING_VALOR_USADA_KEY] = float(a.preco_fipe)
            st.toast(f"Moto usada será {brl(a.preco_fipe)} na sidebar")
            st.rerun()
