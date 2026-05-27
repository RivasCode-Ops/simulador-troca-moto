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
    peso_exibicao_pct,
    peso_total_ativo,
)
from src.exportacao import exportar_csv, exportar_json  # noqa: E402
from src.fipe_ui import SESSION_FIPE, render_consulta_fipe  # noqa: E402
from src.historico import (  # noqa: E402
    PERSIST_KEY,
    SESSION_KEY,
    adicionar_ao_historico,
    comparar_duas_para_exibicao,
    criar_snapshot,
    dados_grafico_comparacao,
    delta_vs_ultimo_salvo,
    linhas_comparacao,
    listar_opcoes_comparacao,
    rotulo_completo,
)
from src.persistencia import carregar as carregar_persistido  # noqa: E402
from src.persistencia import excluir as excluir_persistido  # noqa: E402
from src.persistencia import limpar_todos as limpar_persistido  # noqa: E402
from src.persistencia import salvar as salvar_persistido  # noqa: E402
from src.operacao import DadosOperacao, simular_troca  # noqa: E402
from src.relatorio import montar_relatorio  # noqa: E402
from src.relatorio_ui import render_relatorio_simulacao  # noqa: E402
from src.sessao_ui import SNAPSHOT_PENDENTE_KEY, aplicar_pendentes_sidebar  # noqa: E402
from src.ui import (  # noqa: E402
    brl,
    delta_brl,
    pct,
    progresso_normalizado,
    rotulo_kpi_risco,
    tabela_amortizacao,
    tabela_cenarios_exibicao,
    html_banner_semaforo,
    md_escape,
)
from src.validacao import tem_erro_bloqueante, validar_entradas  # noqa: E402

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
        background: rgba(255, 255, 255, 0.06);
        padding: 0.65rem 0.85rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        min-height: 4.75rem;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {
        color: #f1f5f9 !important;
        fill: #f1f5f9 !important;
    }
    div[data-testid="stMetric"] label {
        white-space: normal !important;
        line-height: 1.25;
        overflow: visible !important;
        text-overflow: clip !important;
        max-width: 100%;
        word-break: break-word;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.15rem;
        overflow-wrap: anywhere;
        color: #ffffff !important;
    }
    @media (prefers-color-scheme: light) {
        div[data-testid="stMetric"] {
            background: #f1f5f9;
            border-color: #e2e8f0;
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #0f172a !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #020617 !important;
        }
    }
    @media (max-width: 900px) {
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

aplicar_pendentes_sidebar()

# ── Sidebar: apenas drivers globais ─────────────────────────────────────────
with st.sidebar:
    st.title("Parâmetros")
    valor_usada = st.number_input(
        "Moto usada (R$)", 0.0, 500_000.0, 25_000.0, 500.0, key="valor_usada"
    )
    valor_nova = st.number_input("Moto nova (R$)", 0.0, 500_000.0, 30_000.0, 500.0, key="valor_nova")
    entrada_comprador = st.number_input(
        "Entrada do comprador (R$)", 0.0, 500_000.0, 20_000.0, 500.0, key="entrada_comprador"
    )
    entrada_loja = st.number_input("Entrada na loja (R$)", 0.0, 500_000.0, 20_000.0, 500.0, key="entrada_loja")

    with st.expander("Financiamento do comprador", expanded=False):
        taxa_venda = st.slider("Juros a.m. (%)", 0.0, 5.0, 2.0, 0.1, key="tv")
        prazo_venda = st.selectbox("Prazo (meses)", [12, 18, 24, 36, 48], index=2, key="pv")
        taxas_venda = st.number_input("TAC venda (R$)", 0.0, 10_000.0, 0.0, 50.0, key="tacv")
        libera_saldo = st.checkbox("Libera saldo financiado na hora", value=True, key="lib")

    with st.expander("Financiamento da moto nova", expanded=False):
        taxa_compra = st.slider("Juros a.m. (%)", 0.0, 5.0, 2.0, 0.1, key="tc")
        prazo_compra = st.selectbox("Prazo (meses)", [12, 18, 24, 36, 48], index=3, key="pc")
        taxas_compra = st.number_input("TAC compra (R$)", 0.0, 10_000.0, 500.0, 50.0, key="tacc")
        cet_manual = st.number_input(
            "Taxa efetiva anual informada (%, 0=calc.)", 0.0, 200.0, 0.0, 0.5, key="cet"
        )

    saldo_venda = max(0.0, valor_usada - entrada_comprador)
    saldo_compra = max(0.0, valor_nova - entrada_loja)
    st.markdown(
        f'<p style="font-size:0.85rem;color:#64748b;margin:0;">'
        f"Saldo comprador: {brl(saldo_venda)} · Seu saldo: {brl(saldo_compra)}"
        f"</p>",
        unsafe_allow_html=True,
    )

    avisos_dom = validar_entradas(
        valor_usada,
        valor_nova,
        entrada_comprador,
        entrada_loja,
        taxa_venda,
        taxa_compra,
        prazo_venda,
        prazo_compra,
    )
    for av in avisos_dom:
        if av.nivel == "erro":
            st.error(av.mensagem)
        elif av.nivel == "aviso":
            st.warning(av.mensagem)
        else:
            st.info(av.mensagem)

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
        usar_cet_limite = st.checkbox("Limitar taxa efetiva anual", value=False, key="lim_cet_on")
        cet_max = (
            st.number_input("Taxa efetiva máx. (% a.a.)", 0.0, 200.0, 40.0, 1.0, key="lim_cet")
            if usar_cet_limite
            else 0.0
        )

if PERSIST_KEY not in st.session_state:
    st.session_state[PERSIST_KEY] = carregar_persistido()
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

bloqueio_dom = tem_erro_bloqueante(avisos_dom)

if bloqueio_dom:
    troca = None
    cenarios = []
    export_rows = []
else:
    troca = simular_troca(dados)
    cenarios = listar_cenarios(premissas)
    export_rows = cenarios_para_exportacao(cenarios)

# ── Main: KPIs + decisão ───────────────────────────────────────────────────
st.title("🏍️ Troca de moto — decisão financeira")
st.caption("Simulador de dupla ponta · venda da usada + compra da nova")

if bloqueio_dom:
    st.error("Corrija os parâmetros na barra lateral para ver a simulação.")
    st.stop()

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
fipe_sessao = st.session_state.get(SESSION_FIPE)
limites_snap = {
    "custo_extra_max": custo_extra_max,
    "parcela_max": parcela_max,
    "prazo_max_saldo": prazo_max_saldo,
    "entrada_min": entrada_min,
    "usar_limites": usar_limites,
}
atual_snap = criar_snapshot(
    "Atual",
    dados,
    troca,
    decisao,
    fipe=fipe_sessao,
    limites_extra=limites_snap,
)
historico_sessao = st.session_state[SESSION_KEY]
historico_persist = st.session_state[PERSIST_KEY]
historico = historico_persist

# 4 KPIs principais
k1, k2, k3, k4 = st.columns(4)
k1.metric("Custo extra", brl(troca.custo_extra_vs_ideal))
k2.metric("Parcela nova", brl(troca.compra.parcela_moto_nova))
k3.metric("Receb. usada", brl(troca.venda.total_recebido_pelo_vendedor))
k4.metric("Risco", rotulo_kpi_risco(decisao))

cor = cor_semaforo(decisao.semaforo)
st.markdown(html_banner_semaforo(decisao, cor), unsafe_allow_html=True)

st.subheader("Relatório da simulação")
relatorio = montar_relatorio(
    dados=dados,
    troca=troca,
    decisao=decisao,
    limites=limites,
    explicacao=explicacao,
    fipe=fipe_sessao,
)
render_relatorio_simulacao(relatorio)

render_consulta_fipe(valor_usada, troca.custo_extra_vs_ideal)

with st.expander("📋 Histórico salvo (persistente)", expanded=bool(historico)):
    rotulo_save = st.text_input("Nome da simulação", placeholder="Ex.: Proposta loja X", key="rotulo_hist")
    h1, h2, h3 = st.columns(3)
    if h1.button("Salvar no disco", type="primary"):
        snap = criar_snapshot(
            rotulo_save,
            dados,
            troca,
            decisao,
            fipe=fipe_sessao,
            limites_extra=limites_snap,
        )
        salvar_persistido(snap)
        st.session_state[PERSIST_KEY] = carregar_persistido()
        st.session_state[SESSION_KEY] = adicionar_ao_historico(historico_sessao, snap)
        st.session_state["cmp_b"] = rotulo_completo(snap)
        st.success(f"Simulação salva: {snap['rotulo']}")
        st.toast(f"Salvo em data/simulacoes.json")
        st.rerun()
    if h2.button("Limpar tudo no disco", disabled=not historico):
        limpar_persistido()
        st.session_state[PERSIST_KEY] = []
        st.session_state[SESSION_KEY] = []
        st.rerun()
    if h3.button("Recarregar lista"):
        st.session_state[PERSIST_KEY] = carregar_persistido()
        st.rerun()
    st.caption(
        f"Arquivo local: `data/simulacoes.json` · {len(historico)} registro(s) · "
        "inclui consulta FIPE quando disponível"
    )

    if historico:
        opcoes_restaurar = {rotulo_completo(s): s for s in historico}
        rotulos_rest = list(opcoes_restaurar.keys())
        sel_rest = st.selectbox("Reabrir simulação salva", rotulos_rest, key="hist_restaurar")
        c_rest, c_del = st.columns(2)
        if c_rest.button("Carregar parâmetros na sidebar"):
            st.session_state[SNAPSHOT_PENDENTE_KEY] = opcoes_restaurar[sel_rest]
            st.toast("Carregando parâmetros na sidebar…")
            st.rerun()
        if c_del.button("Excluir selecionada"):
            reg = opcoes_restaurar[sel_rest]
            excluir_persistido(reg["id"])
            st.session_state[PERSIST_KEY] = carregar_persistido()
            st.toast(f"Removido: {reg['rotulo']}")
            st.rerun()
    df_hist = pd.DataFrame(linhas_comparacao(atual_snap, historico))
    st.dataframe(
        df_hist,
        use_container_width=True,
        hide_index=True,
        column_config={
            "FIPE": st.column_config.TextColumn("FIPE", width="medium"),
            "Nome": st.column_config.TextColumn("Nome", width="small"),
        },
    )
    deltas = delta_vs_ultimo_salvo(atual_snap, historico)
    if deltas:
        st.markdown(
            md_escape(
                f"Δ vs última salva: custo extra {delta_brl(deltas['custo_extra'])} · "
                f"parcela {delta_brl(deltas['parcela_nova'])}"
            )
        )

    opcoes = listar_opcoes_comparacao(atual_snap, historico)
    if len(opcoes) >= 2:
        st.markdown("**Comparar duas simulações**")
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
            df_cmp = comparar_duas_para_exibicao(sa, sb, nome_a, nome_b)
            st.dataframe(df_cmp, use_container_width=True, hide_index=True)
            chart = dados_grafico_comparacao(sa, sb, nome_a, nome_b)
            st.bar_chart(pd.DataFrame(chart).set_index("Métrica")[[nome_a, nome_b]])
            melhor_custo = nome_a if sa["custo_extra"] <= sb["custo_extra"] else nome_b
            st.caption(f"Menor custo extra neste par: **{melhor_custo}**")

with st.expander("🚦 Análise do semáforo", expanded=decisao.semaforo != Semaforo.VERDE):
    if limites.usar_limites and decisao.criterios:
        peso_total = peso_total_ativo(decisao.criterios)
        st.progress(progresso_normalizado(decisao.pontuacao_risco))
        st.caption(
            f"Pontuação de risco: **{decisao.pontuacao_risco:.0f}/100** "
            f"(pesos ativos somam {peso_total:.0f} → normalizados para 100)"
        )
        df_crit = pd.DataFrame(
            [
                {
                    "": icone_severidade(c.severidade),
                    "Critério": c.nome,
                    "Peso": (
                        f"{peso_exibicao_pct(c, peso_total):.0f}%"
                        if c.peso > 0
                        else "—"
                    ),
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
        st.progress(progresso_normalizado(decisao.pct_custo_extra_do_limite))
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
        st.dataframe(tabela_amortizacao(v.financiamento.tabela), use_container_width=True, hide_index=True)

# ── Bloco 3: Compra ──────────────────────────────────────────────────────────
st.header("3 · Compra da nova")
cp = troca.compra
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor financiado", brl(cp.financiamento.valor_financiado))
c2.metric("Parcela", brl(cp.parcela_moto_nova))
c3.metric("Total pago ao banco", brl(cp.total_pago_banco))
c4.metric("Juros totais", brl(cp.juros_totais))
fin = cp.financiamento
st.markdown(
    md_escape(
        f"Juros: {pct(fin.taxa_mensal * 100)} ao mês · "
        f"Nominal a.a.: {pct(fin.taxa_nominal_anual_pct)} · "
        f"Efetiva a.a. (calc.): {pct(fin.taxa_efetiva_anual_pct)} · "
        f"Custo total no prazo (sobre principal): {pct(fin.custo_total_prazo_pct)} · "
        f"Informada: {pct(cp.cet_informado_pct) if cp.cet_informado_pct else '—'}"
    )
)
tab_t, tab_g = st.tabs(["Tabela", "Gráfico"])
df_amort_raw = pd.DataFrame(cp.financiamento.tabela)
with tab_t:
    st.dataframe(tabela_amortizacao(cp.financiamento.tabela), use_container_width=True, hide_index=True)
with tab_g:
    if not df_amort_raw.empty:
        st.line_chart(df_amort_raw.set_index("parcela")[["saldo", "juros"]])

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
st.dataframe(tabela_cenarios_exibicao(df_cen), use_container_width=True, hide_index=True)

alt = [c for c in cenarios if c.id != "ideal" and c.id != "plano_atual"]
if alt:
    melhor = min(alt, key=lambda x: x.custo_extra_vs_ideal)
    st.info(
        md_escape(
            f"**Melhor alternativa:** {melhor.nome} — custo extra {brl(melhor.custo_extra_vs_ideal)}"
        )
    )

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
