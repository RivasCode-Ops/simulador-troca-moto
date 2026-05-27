"""Utilitários de formatação e exibição (pt-BR)."""

from __future__ import annotations

import html
import pandas as pd

from .decisao import ResultadoDecisao, Severidade, Semaforo, Veredito

_COLUNAS_AMORTIZACAO = {
    "parcela": "Parcela",
    "pagamento": "Pagamento",
    "juros": "Juros",
    "amortizacao": "Amortização",
    "saldo": "Saldo",
}


def _pt_num(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(valor: float) -> str:
    return f"R$ {_pt_num(valor)}"


def pct(valor: float, casas: int = 2) -> str:
    return f"{_pt_num(valor, casas)}%"


def delta_brl(valor: float) -> str:
    if valor >= 0:
        return f"+{brl(valor)}"
    return f"-{brl(abs(valor))}"


def md_escape(texto: str) -> str:
    """Escapa $ para não quebrar Markdown/LaTeX do Streamlit em captions."""
    return texto.replace("$", r"\$")


def progresso_normalizado(pct: float | None) -> float:
    """Converte percentual (pode ser negativo) em fração 0–1 para st.progress."""
    if pct is None:
        return 0.0
    return max(0.0, min(float(pct) / 100.0, 1.0))


_TITULO_BANNER = {
    Semaforo.VERDE: "Aprovado",
    Semaforo.AMARELO: "Atenção",
    Semaforo.VERMELHO: "Reprovado",
}


def mensagem_banner_resumo(decisao: ResultadoDecisao) -> str:
    """Mensagem do banner alinhada ao semáforo (não reutiliza texto de critérios críticos)."""
    if decisao.veredito == Veredito.INDEFINIDO and not decisao.criterios:
        return decisao.mensagem

    if decisao.semaforo == Semaforo.VERDE:
        return (
            f"Dentro dos limites (risco {decisao.pontuacao_risco:.0f}/100). "
            "Compare com cenários salvos no histórico."
        )
    if decisao.semaforo == Semaforo.AMARELO:
        n = len(decisao.motivos_atencao)
        if n:
            return (
                f"Risco {decisao.pontuacao_risco:.0f}/100 — {n} alerta(s) intermediário(s). "
                "Negocie antes de assinar."
            )
        return f"Risco {decisao.pontuacao_risco:.0f}/100 — negocie condições antes de assinar."

    ids = {c.id for c in decisao.criterios if c.severidade == Severidade.CRITICO}
    if "custo_extra" in ids and "parcela" in ids:
        return "Custo extra e parcela acima dos limites — não feche sem renegociar."
    if "custo_extra" in ids:
        return "Custo extra acima do limite — renegocie juros, prazo ou entrada do comprador."
    if "parcela" in ids:
        return "Parcela da moto nova acima do teto — ajuste entrada ou prazo."
    if decisao.motivos_falha:
        if len(decisao.motivos_falha) == 1:
            return decisao.motivos_falha[0]
        return (
            f"{len(decisao.motivos_falha)} critérios críticos — "
            "veja detalhes na análise do semáforo."
        )
    return "Operação fora dos limites definidos na seção H."


def html_banner_semaforo(decisao: ResultadoDecisao, cor: str) -> str:
    titulo = _TITULO_BANNER[decisao.semaforo]
    msg = mensagem_banner_resumo(decisao)
    return (
        f'<div class="semaforo-box" style="background:{cor}18;border-left:5px solid {cor};">'
        f"<strong>{html.escape(titulo)}</strong> — {html.escape(msg)}</div>"
    )


def rotulo_kpi_risco(decisao: ResultadoDecisao) -> str:
    emoji = {Semaforo.VERDE: "🟢", Semaforo.AMARELO: "🟡", Semaforo.VERMELHO: "🔴"}[decisao.semaforo]
    rotulo_curto = decisao.veredito.value.split("—")[0].strip()
    return f"{decisao.pontuacao_risco:.0f}/100 · {emoji} {rotulo_curto}"


def tabela_amortizacao(tabela: list[dict]) -> pd.DataFrame:
    if not tabela:
        return pd.DataFrame(columns=list(_COLUNAS_AMORTIZACAO.values()))
    df = pd.DataFrame(tabela).rename(columns=_COLUNAS_AMORTIZACAO)
    for col in ("Pagamento", "Juros", "Amortização", "Saldo"):
        if col in df.columns:
            df[col] = df[col].map(lambda v: brl(float(v)) if pd.notna(v) else "—")
    return df


def tabela_cenarios_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    """Formata cenários para exibição sem Styler (pt-BR)."""
    if df.empty:
        return df
    out = df.copy()
    for col in ("À vista", "Total", "Parcela nova", "Custo extra"):
        if col in out.columns:
            out[col] = out[col].map(lambda v: brl(float(v)) if pd.notna(v) else "—")
    return out
