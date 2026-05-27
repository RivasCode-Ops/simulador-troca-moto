"""
Dashboard de decisão — troca de moto (dupla ponta).
Rodar: streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.cenarios import cenarios_para_exportacao, listar_cenarios, premissas_from_inputs  # noqa: E402
from src.decisao import (  # noqa: E402
    LimitesDecisao,
    Semaforo,
    avaliar_decisao,
    cor_semaforo,
    explicar_custo_extra,
    icone_severidade,
)
from src.exportacao import exportar_csv, exportar_json  # noqa: E402
from src.historico import (  # noqa: E402
    MAX_SNAPSHOTS_SESSAO,
    SESSION_KEY,
    adicionar_ao_historico,
    comparar_duas,
    criar_snapshot,
    dados_grafico_comparacao,
    delta_vs_ultimo_salvo,
    linhas_comparacao,
    listar_opcoes_comparacao,
    rotulo_completo,
)
from src.operacao import DadosOperacao, simular_troca  # noqa: E402
from src.ui import brl, pct  # noqa: E402

st.set_page_config(
    page_title="Troca de Moto — Decisão",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .semaforo-box {
        padding: 1rem 1.25rem;
        border-radius: 10px;
        margin-bottom: 0.75rem;
        font-size: 1rem;
    }
    div[data-testid="stMetric"] {
        background: #f1f5f9;
        padding: 0.65rem 0.85rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar: apenas drivers globais ─────────────────────────────────────────
with st.sidebar:
    st.title("Parâmetros")
    valor_usada = st.number_input("Moto usada (R$)", 0.0, 500_000.0, 25_000.0, 500.0)
    valor_nova = st.number_input("Moto nova (R$)", 0.0, 500_000.0, 30_000.0, 500.0)
    entrada_comprador = st.number_input("Entrada do comprador (R$)", 0.0, 500_000.0, 20_000.0, 500.0)
    entrada_loja = st.number_input("Entrada na loja (R$)", 0.0, 500_000.0, 20_000.0, 500.0)

    with st.expander("Financiamento do comprador", expanded=False):
        taxa_venda = st.slider("Juros a.m. (%)", 0.0, 5.0, 2.0, 0.1, key="tv")
        prazo_venda = st.selectbox("Prazo (meses)", [12, 18, 24, 36, 48], index=2, key="pv")
        taxas_venda = st.number_input("TAC venda (R$)", 0.0, 10_000.0, 0.0, 50.0, key="tacv")
        libera_saldo = st.checkbox("Libera saldo financiado na hora", value=True, key="lib")

    with st.expander("Financiamento da moto nova", expanded=False):
        taxa_compra = st.slider("Juros a.m. (%)", 0.0, 5.0, 2.0, 0.1, key="tc")
        prazo_compra = st.selectbox("Prazo (meses)", [12, 18, 24, 36, 48], index=3, key="pc")
        taxas_compra = st.number_input("TAC compra (R$)", 0.0, 10_000.0, 500.0, 50.0, key="tacc")
        cet_manual = st.number_input("CET loja (%, 0=calc.)", 0.0, 200.0, 0.0, 0.5, key="cet")

    saldo_venda = max(0.0, valor_usada - entrada_comprador)
    saldo_compra = max(0.0, valor_nova - entrada_loja)
    st.caption(f"Saldo comprador: **{brl(saldo_venda)}** · Seu saldo: **{brl(saldo_compra)}**")

    with st.expander("Limites de decisão (seção H)", expanded=False):
        usar_limites = st.checkbox("Ativar semáforo", value=True, key="lim_ativo")
        custo_extra_max = st.number_input("Custo extra máx. (R$)", 0.0, 50_000.0, 4_000.0, 100.0, key="lim_ce")
        parcela_max = st.number_input("Parcela máx. nova (R$)", 0.0, 10_000.0, 450.0, 10.0, key="lim_par")
        prazo_max_saldo = st.selectbox(
            "Prazo máx. saldo financ.",
            [0, 1, 3, 6, 12, 24],
            format_func=lambda x: "Imediato" if x == 0 else f"{x} m",
            key="lim_prazo",
        )
        entrada_min = st.number_input("Entrada mín. comprador (R$)", 0.0, 500_000.0, 20_000.0, 500.0, key="lim_ent")
        usar_cet_limite = st.checkbox("Limitar CET", value=False, key="lim_cet_on")
        cet_max = st.number_input("CET máx. (%)", 0.0, 200.0, 40.0, 1.0, key="lim_cet") if usar_cet_limite else 0.0

if SESSION_KEY not in st.session_state:
    st.session_state[SESSION_KEY] = []

dados = DadosOperacao(
    valor_moto_usada=valor_usada,
    valor_moto_nova=valor_nova,
    entrada_comprador=entrada_comprador,
    entrada_loja=entrada_loja,
    taxa_venda_mensal_pct=taxa_venda,
    prazo_venda_meses=prazo_venda,
    taxa_compra_mensal_pct=taxa_compra,
    prazo_compra_meses=prazo_compra,
    taxas_contrato_venda=taxas_venda,
    taxas_contrato_compra=taxas_compra,
    comprador_libera_saldo_na_hora=libera_saldo,
    cet_compra_informado_pct=cet_manual if cet_manual > 0 else None,
)

premissas = premissas_from_inputs(
    valor_usada, valor_nova, entrada_comprador, entrada_loja,
    taxa_venda, taxa_compra, prazo_venda, prazo_compra, taxas_venda, taxas_compra, libera_saldo,
)

troca = simular_troca(dados)
cenarios = listar_cenarios(premissas)
export_rows = cenarios_para_exportacao(cenarios)

# ── Main: KPIs + decisão ───────────────────────────────────────────────────
st.title("🏍️ Troca de moto — decisão financeira")
st.caption("Simulador de dupla ponta · venda da usada + compra da nova")

limites = LimitesDecisao(
    custo_extra_maximo=custo_extra_max,
    parcela_maxima_nova=parcela_max,
    prazo_max_receber_saldo_meses=prazo_max_saldo,
    cet_maximo_tolerado_pct=cet_max if usar_cet_limite else None,
    entrada_minima_comprador=entrada_min,
    usar_limites=usar_limites,
)
decisao = avaliar_decisao(troca, limites)
explicacao = explicar_custo_extra(troca)
atual_snap = criar_snapshot("Atual", dados, troca, decisao)
historico = st.session_state[SESSION_KEY]

emoji_status = {"verde": "🟢", "amarelo": "🟡", "vermelho": "🔴"}[decisao.semaforo.value]

# 4 KPIs principais
k1, k2, k3, k4 = st.columns(4)
k1.metric("Custo extra da troca", brl(troca.custo_extra_vs_ideal))
k2.metric("Parcela moto nova", brl(troca.compra.parcela_moto_nova))
k3.metric("Total a receber (usada)", brl(troca.venda.total_recebido_pelo_vendedor))
k4.metric("Risco / Status", f"{decisao.pontuacao_risco:.0f}/100 · {emoji_status}")

cor = cor_semaforo(decisao.semaforo)
st.markdown(
    f'<div class="semaforo-box" style="background:{cor}18;border-left:5px solid {cor};">'
    f"<strong>{decisao.veredito.value}</strong> — {decisao.mensagem}</div>",
    unsafe_allow_html=True,
)

with st.expander("📋 Histórico desta sessão", expanded=bool(historico)):
    rotulo_save = st.text_input("Nome da simulação", placeholder="Ex.: Proposta loja X", key="rotulo_hist")
    h1, h2 = st.columns(2)
    if h1.button("Salvar simulação", type="primary"):
        snap = criar_snapshot(rotulo_save, dados, troca, decisao)
        st.session_state[SESSION_KEY] = adicionar_ao_historico(historico, snap)
        st.toast(f"Salvo: {snap['rotulo']}")
        st.rerun()
    if h2.button("Limpar histórico", disabled=not historico):
        st.session_state[SESSION_KEY] = []
        st.rerun()
    st.caption(f"Até {MAX_SNAPSHOTS_SESSAO} simulações nesta sessão · {len(historico)} salva(s)")
    df_hist = pd.DataFrame(linhas_comparacao(atual_snap, historico))
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
    deltas = delta_vs_ultimo_salvo(atual_snap, historico)
    if deltas:
        st.caption(
            f"Δ em relação à última salva: custo extra {deltas['custo_extra']:+,.2f} · "
            f"parcela {deltas['parcela_nova']:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    opcoes = listar_opcoes_comparacao(atual_snap, historico)
    if len(opcoes) >= 2:
        st.markdown("**Comparar duas simulações lado a lado**")
        labels = []
        snaps: dict[str, dict] = {}
        for oid, snap in opcoes:
            if oid == "atual":
                lbl = "Atual (agora)"
            else:
                lbl = rotulo_completo(snap)
            labels.append(lbl)
            snaps[lbl] = snap

        c_a, c_b = st.columns(2)
        nome_a = c_a.selectbox("Simulação A", labels, index=0, key="cmp_a")
        nome_b = c_b.selectbox(
            "Simulação B",
            labels,
            index=min(1, len(labels) - 1),
            key="cmp_b",
        )
        if nome_a == nome_b:
            st.warning("Escolha duas simulações diferentes para comparar.")
        else:
            sa, sb = snaps[nome_a], snaps[nome_b]
            df_cmp = pd.DataFrame(comparar_duas(sa, sb, nome_a, nome_b))
            st.dataframe(
                df_cmp.style.format(
                    {nome_a: "{:,.2f}", nome_b: "{:,.2f}", "Delta (B − A)": "{:+,.2f}"},
                    decimal=",",
                    thousands=".",
                    na_rep="—",
                ),
                use_container_width=True,
                hide_index=True,
            )
            chart = dados_grafico_comparacao(sa, sb, nome_a, nome_b)
            st.bar_chart(pd.DataFrame(chart).set_index("Métrica")[[nome_a, nome_b]])
            melhor_custo = nome_a if sa["custo_extra"] <= sb["custo_extra"] else nome_b
            st.caption(f"Menor custo extra neste par: **{melhor_custo}**")

with st.expander("🚦 Análise do semáforo", expanded=decisao.semaforo != Semaforo.VERDE):
    if limites.usar_limites and decisao.criterios:
        st.progress(min(decisao.pontuacao_risco / 100, 1.0))
        st.caption(f"Pontuação de risco: **{decisao.pontuacao_risco:.0f}/100** (peso por critério da seção H)")
        df_crit = pd.DataFrame(
            [
                {
                    "": icone_severidade(c.severidade),
                    "Critério": c.nome,
                    "Peso": f"{c.peso}%",
                    "Uso do limite": f"{c.pct_do_limite:.0f}%",
                    "Status": c.status_label,
                    "Mensagem": c.mensagem,
                }
                for c in decisao.criterios
            ]
        )
        st.dataframe(df_crit, use_container_width=True, hide_index=True)
        if decisao.resumo_acoes:
            st.markdown("**O que fazer agora:**")
            for acao in decisao.resumo_acoes:
                st.markdown(f"- {acao}")
    else:
        st.info("Ative os limites na seção H para ver critérios, pesos e severidade.")

with st.expander("📐 Como calculamos o custo extra", expanded=False):
    st.markdown(f"**{explicacao.formula_texto}**")
    for linha in explicacao.detalhe_linhas:
        st.markdown(f"- {linha}")
    if decisao.pct_custo_extra_do_limite is not None:
        st.progress(min(decisao.pct_custo_extra_do_limite / 100, 1.0))
        st.caption(f"Custo extra = {decisao.pct_custo_extra_do_limite:.0f}% do limite máximo definido")

# ── Bloco 2: Venda ───────────────────────────────────────────────────────────
st.header("2 · Venda da usada")
v = troca.venda
r1, r2, r3, r4 = st.columns(4)
r1.metric("Entrada à vista", brl(v.entrada_vista))
r2.metric("Saldo financiado", brl(v.saldo_financiado))
r3.metric("Parcela do comprador", brl(v.parcela_comprador))
r4.metric("Total que você recebe", brl(v.total_recebido_pelo_vendedor))
st.caption(v.observacao_recebimento)
if v.financiamento and v.saldo_financiado > 0:
    with st.expander("Amortização — comprador"):
        st.dataframe(pd.DataFrame(v.financiamento.tabela), use_container_width=True, hide_index=True)

# ── Bloco 3: Compra ──────────────────────────────────────────────────────────
st.header("3 · Compra da nova")
cp = troca.compra
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor financiado", brl(cp.financiamento.valor_financiado))
c2.metric("Parcela", brl(cp.parcela_moto_nova))
c3.metric("Total pago ao banco", brl(cp.total_pago_banco))
c4.metric("Juros totais", brl(cp.juros_totais))
st.caption(f"CET calc.: {pct(cp.cet_calculado_pct)} · CET informado: {pct(cp.cet_informado_pct) if cp.cet_informado_pct else '—'}")
tab_t, tab_g = st.tabs(["Tabela", "Gráfico"])
df_amort = pd.DataFrame(cp.financiamento.tabela)
with tab_t:
    st.dataframe(df_amort, use_container_width=True, hide_index=True)
with tab_g:
    if not df_amort.empty:
        st.line_chart(df_amort.set_index("parcela")[["saldo", "juros"]])

# ── Bloco 4: Comparação e cenários ───────────────────────────────────────────
st.header("4 · Comparação e cenários")

df_cen = pd.DataFrame(
    [
        {
            "Cenário": c.nome,
            "À vista": c.desembolso_vista_ideal,
            "Total": c.total_desembolsado,
            "Parcela nova": c.parcela_compra or 0,
            "Custo extra": c.custo_extra_vs_ideal,
            "Nota": c.observacao,
        }
        for c in cenarios
    ]
)
st.dataframe(
    df_cen.style.highlight_max(subset=["Custo extra"], color="#fecaca").format(
        {
            "À vista": "{:,.2f}",
            "Total": "{:,.2f}",
            "Parcela nova": "{:,.2f}",
            "Custo extra": "{:,.2f}",
        },
        decimal=",",
        thousands=".",
    ),
    use_container_width=True,
    hide_index=True,
)

alt = [c for c in cenarios if c.id != "ideal" and c.id != "plano_atual"]
if alt:
    melhor = min(alt, key=lambda x: x.custo_extra_vs_ideal)
    st.info(f"**Melhor alternativa:** {melhor.nome} — custo extra {brl(melhor.custo_extra_vs_ideal)}")

# Exportação
st.subheader("Exportar simulação")
ex1, ex2 = st.columns(2)
meta = {
    "moto_usada": valor_usada,
    "moto_nova": valor_nova,
    "semaforo": decisao.semaforo.value,
    "custo_extra": troca.custo_extra_vs_ideal,
}
ex1.download_button(
    "Baixar cenários (CSV)",
    data=exportar_csv(export_rows),
    file_name="troca_moto_cenarios.csv",
    mime="text/csv",
)
ex2.download_button(
    "Baixar cenários (JSON)",
    data=exportar_json(export_rows, meta),
    file_name="troca_moto_cenarios.json",
    mime="application/json",
)

st.divider()
st.caption("MVP local · Não é recomendação financeira · `docs/MODELAGEM.md`")
