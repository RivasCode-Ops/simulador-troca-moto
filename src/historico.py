"""Histórico de simulações (sessão e persistência)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .decisao import ResultadoDecisao
from .fipe_analise import AnaliseFipeVenda
from .operacao import DadosOperacao, ResultadoTroca
from .ui import brl

MAX_SNAPSHOTS_SESSAO = 5
SESSION_KEY = "historico_simulacoes"
PERSIST_KEY = "historico_persistente"

METRICAS_COMPARACAO: list[tuple[str, str]] = [
    ("custo_extra", "Custo extra"),
    ("parcela_nova", "Parcela moto nova"),
    ("total_receber_usada", "Total a receber (usada)"),
    ("total_desembolsado", "Total pago / desembolsado"),
    ("juros_totais", "Juros (seu bolso)"),
]


@dataclass(frozen=True)
class SnapshotSimulacao:
    rotulo: str
    salvo_em: str
    salvo_em_iso: str
    moto_usada: float
    moto_nova: float
    entrada_comprador: float
    entrada_loja: float
    taxa_compra_pct: float
    prazo_compra_meses: int
    taxa_venda_pct: float
    prazo_venda_meses: int
    taxas_venda: float
    taxas_compra: float
    libera_saldo: bool
    cet_manual: float
    custo_extra: float
    parcela_nova: float
    total_receber_usada: float
    total_desembolsado: float
    juros_totais: float
    semaforo: str
    pontuacao_risco: float
    veredito: str
    mensagem_decisao: str
    preco_alvo_usada: float
    custo_extra_max: float
    parcela_max: float
    prazo_max_saldo: int
    entrada_min: float
    usar_limites: bool

    def para_dict(self) -> dict:
        return asdict(self)


def _fipe_para_dict(fipe: AnaliseFipeVenda | dict[str, Any] | None) -> dict[str, Any] | None:
    if fipe is None:
        return None
    if isinstance(fipe, dict):
        return fipe
    return fipe.para_dict()


def criar_snapshot(
    rotulo: str,
    dados: DadosOperacao,
    troca: ResultadoTroca,
    decisao: ResultadoDecisao,
    *,
    fipe: AnaliseFipeVenda | dict[str, Any] | None = None,
    limites_extra: dict[str, Any] | None = None,
) -> dict:
    lim = limites_extra or {}
    agora = datetime.now()
    snap = SnapshotSimulacao(
        rotulo=rotulo.strip() or "Sem nome",
        salvo_em=agora.strftime("%d/%m %H:%M"),
        salvo_em_iso=agora.isoformat(timespec="seconds"),
        moto_usada=dados.valor_moto_usada,
        moto_nova=dados.valor_moto_nova,
        entrada_comprador=dados.entrada_comprador,
        entrada_loja=dados.entrada_loja,
        taxa_compra_pct=dados.taxa_compra_mensal_pct,
        prazo_compra_meses=dados.prazo_compra_meses,
        taxa_venda_pct=dados.taxa_venda_mensal_pct,
        prazo_venda_meses=dados.prazo_venda_meses,
        taxas_venda=dados.taxas_contrato_venda,
        taxas_compra=dados.taxas_contrato_compra,
        libera_saldo=dados.comprador_libera_saldo_na_hora,
        cet_manual=dados.cet_compra_informado_pct or 0.0,
        custo_extra=troca.custo_extra_vs_ideal,
        parcela_nova=troca.compra.parcela_moto_nova,
        total_receber_usada=troca.venda.total_recebido_pelo_vendedor,
        total_desembolsado=troca.total_desembolsado_operacao,
        juros_totais=troca.juros_total_seu_bolso,
        semaforo=decisao.semaforo.value,
        pontuacao_risco=decisao.pontuacao_risco,
        veredito=decisao.veredito.value,
        mensagem_decisao=decisao.mensagem,
        preco_alvo_usada=dados.valor_moto_usada,
        custo_extra_max=float(lim.get("custo_extra_max", 4_000.0)),
        parcela_max=float(lim.get("parcela_max", 450.0)),
        prazo_max_saldo=int(lim.get("prazo_max_saldo", 0)),
        entrada_min=float(lim.get("entrada_min", 20_000.0)),
        usar_limites=bool(lim.get("usar_limites", True)),
    )
    out = snap.para_dict()
    out["id"] = str(uuid.uuid4())
    fipe_d = _fipe_para_dict(fipe)
    if fipe_d:
        out["fipe"] = fipe_d
    return out


def aplicar_snapshot_na_sessao(snap: dict) -> None:
    """Restaura parâmetros da sidebar (chamar antes do rerun)."""
    import streamlit as st

    st.session_state["valor_usada"] = float(snap["moto_usada"])
    st.session_state["valor_nova"] = float(snap["moto_nova"])
    st.session_state["entrada_comprador"] = float(snap["entrada_comprador"])
    st.session_state["entrada_loja"] = float(snap["entrada_loja"])
    st.session_state["tv"] = float(snap["taxa_venda_pct"])
    st.session_state["pv"] = int(snap["prazo_venda_meses"])
    st.session_state["tacv"] = float(snap.get("taxas_venda", 0))
    st.session_state["lib"] = bool(snap.get("libera_saldo", True))
    st.session_state["tc"] = float(snap["taxa_compra_pct"])
    st.session_state["pc"] = int(snap["prazo_compra_meses"])
    st.session_state["tacc"] = float(snap.get("taxas_compra", 500))
    st.session_state["cet"] = float(snap.get("cet_manual", 0))
    st.session_state["lim_ativo"] = bool(snap.get("usar_limites", True))
    st.session_state["lim_ce"] = float(snap.get("custo_extra_max", 4_000))
    st.session_state["lim_par"] = float(snap.get("parcela_max", 450))
    st.session_state["lim_prazo"] = int(snap.get("prazo_max_saldo", 0))
    st.session_state["lim_ent"] = float(snap.get("entrada_min", 20_000))


def adicionar_ao_historico(historico: list[dict], snapshot: dict) -> list[dict]:
    return [snapshot, *historico][:MAX_SNAPSHOTS_SESSAO]


def rotulo_completo(snap: dict) -> str:
    risco = snap.get("pontuacao_risco")
    extra = f" · risco {risco:.0f}" if risco is not None else ""
    fipe = snap.get("fipe")
    fipe_txt = ""
    if fipe and fipe.get("preco_fipe"):
        fipe_txt = f" · FIPE {fipe['preco_fipe']:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{snap['rotulo']} ({snap['salvo_em']}){extra}{fipe_txt}"


def rotulo_opcao(snap: dict, prefixo: str = "") -> str:
    return f"{prefixo}{snap['rotulo']} ({snap['salvo_em']})"


def listar_opcoes_comparacao(atual: dict, historico: list[dict]) -> list[tuple[str, dict]]:
    opcoes: list[tuple[str, dict]] = [("atual", atual)]
    for i, s in enumerate(historico):
        opcoes.append((s.get("id", f"h{i}"), s))
    return opcoes


def linhas_comparacao(atual: dict, historico: list[dict]) -> list[dict]:
    def _fipe_col(s: dict) -> str:
        f = s.get("fipe")
        if not f:
            return "—"
        pf = f.get("preco_fipe")
        if pf is None:
            return "—"
        return f"R$ {pf:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _veredito_curto(s: dict) -> str:
        v = s.get("veredito")
        if v:
            return str(v).split("—")[0].strip()
        return "—"

    linhas = [
        {
            "Nome": "[Atual]",
            "Quando": "agora",
            "Preço alvo": brl(atual.get("preco_alvo_usada", atual.get("moto_usada", 0))),
            "Custo extra": brl(atual["custo_extra"]),
            "Parcela nova": brl(atual["parcela_nova"]),
            "FIPE": _fipe_col(atual),
            "Risco": f"{atual.get('pontuacao_risco', 0):.0f}/100",
            "Semáforo": atual["semaforo"],
            "Veredito": _veredito_curto(atual),
        }
    ]
    for s in historico:
        linhas.append(
            {
                "Nome": s["rotulo"],
                "Quando": s["salvo_em"],
                "Preço alvo": brl(s.get("preco_alvo_usada", s.get("moto_usada", 0))),
                "Custo extra": brl(s["custo_extra"]),
                "Parcela nova": brl(s["parcela_nova"]),
                "FIPE": _fipe_col(s),
                "Risco": f"{s.get('pontuacao_risco', 0):.0f}/100",
                "Semáforo": s["semaforo"],
                "Veredito": _veredito_curto(s),
            }
        )
    return linhas


LINHAS_TEXTO_COMPARACAO = frozenset({"Semáforo", "Veredito"})


def comparar_duas(a: dict, b: dict, nome_a: str, nome_b: str) -> list[dict]:
    linhas: list[dict] = []
    for chave, titulo in METRICAS_COMPARACAO:
        va = float(a.get(chave, 0))
        vb = float(b.get(chave, 0))
        linhas.append(
            {
                "Métrica": titulo,
                nome_a: va,
                nome_b: vb,
                "Delta (B − A)": round(vb - va, 2),
            }
        )
    fa, fb = a.get("fipe"), b.get("fipe")
    if fa or fb:
        linhas.append(
            {
                "Métrica": "Preço FIPE",
                nome_a: float(fa["preco_fipe"]) if fa else 0,
                nome_b: float(fb["preco_fipe"]) if fb else 0,
                "Delta (B − A)": round(
                    (float(fb["preco_fipe"]) if fb else 0) - (float(fa["preco_fipe"]) if fa else 0),
                    2,
                ),
            }
        )
        if fa and fb:
            linhas.append(
                {
                    "Métrica": "Cobertura custo extra (FIPE)",
                    nome_a: fa.get("cobertura_custo_extra_pct") or 0,
                    nome_b: fb.get("cobertura_custo_extra_pct") or 0,
                    "Delta (B − A)": round(
                        (fb.get("cobertura_custo_extra_pct") or 0)
                        - (fa.get("cobertura_custo_extra_pct") or 0),
                        2,
                    ),
                }
            )
    linhas.append(
        {
            "Métrica": "Score de risco",
            nome_a: float(a.get("pontuacao_risco", 0)),
            nome_b: float(b.get("pontuacao_risco", 0)),
            "Delta (B − A)": round(
                float(b.get("pontuacao_risco", 0)) - float(a.get("pontuacao_risco", 0)),
                1,
            ),
        }
    )
    linhas.append(
        {
            "Métrica": "Semáforo",
            nome_a: a.get("semaforo", "—"),
            nome_b: b.get("semaforo", "—"),
            "Delta (B − A)": "—",
        }
    )
    va = str(a.get("veredito", "")).split("—")[0].strip() or "—"
    vb = str(b.get("veredito", "")).split("—")[0].strip() or "—"
    linhas.append(
        {
            "Métrica": "Veredito",
            nome_a: va,
            nome_b: vb,
            "Delta (B − A)": "—",
        }
    )
    return linhas


def comparar_duas_para_exibicao(a: dict, b: dict, nome_a: str, nome_b: str) -> "pd.DataFrame":
    """Tabela formatada para UI — moeda só em linhas numéricas (evita crash do Styler)."""
    import pandas as pd

    linhas = comparar_duas(a, b, nome_a, nome_b)
    for linha in linhas:
        metrica = linha["Métrica"]
        if metrica in LINHAS_TEXTO_COMPARACAO:
            continue
        if metrica == "Score de risco":
            for col in (nome_a, nome_b):
                val = linha.get(col)
                if isinstance(val, (int, float)):
                    linha[col] = f"{val:.0f}/100"
            delta = linha.get("Delta (B − A)")
            if isinstance(delta, (int, float)):
                sinal = "+" if delta >= 0 else ""
                linha["Delta (B − A)"] = f"{sinal}{abs(delta):.0f}"
            continue
        for col in (nome_a, nome_b):
            val = linha.get(col)
            if isinstance(val, (int, float)):
                linha[col] = brl(float(val))
        delta = linha.get("Delta (B − A)")
        if isinstance(delta, (int, float)):
            sinal = "+" if delta >= 0 else ""
            linha["Delta (B − A)"] = f"{sinal}{delta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return pd.DataFrame(linhas)


def dados_grafico_comparacao(a: dict, b: dict, nome_a: str, nome_b: str) -> dict[str, list]:
    metricas = [titulo for _, titulo in METRICAS_COMPARACAO]
    return {
        "Métrica": metricas,
        nome_a: [float(a.get(chave, 0)) for chave, _ in METRICAS_COMPARACAO],
        nome_b: [float(b.get(chave, 0)) for chave, _ in METRICAS_COMPARACAO],
    }


def delta_vs_ultimo_salvo(atual: dict, historico: list[dict]) -> dict[str, float] | None:
    if not historico:
        return None
    ultimo = historico[0]
    return {
        "custo_extra": round(atual["custo_extra"] - ultimo["custo_extra"], 2),
        "parcela_nova": round(atual["parcela_nova"] - ultimo["parcela_nova"], 2),
    }
