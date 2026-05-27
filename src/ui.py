"""Utilitários de formatação e exibição (pt-BR)."""

from __future__ import annotations

import pandas as pd

from .decisao import ResultadoDecisao, Semaforo

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


def progresso_normalizado(pct: float | None) -> float:
    """Converte percentual (pode ser negativo) em fração 0–1 para st.progress."""
    if pct is None:
        return 0.0
    return max(0.0, min(float(pct) / 100.0, 1.0))


def texto_banner_semaforo(decisao: ResultadoDecisao) -> tuple[str, str]:
    """Título curto + mensagem única (evita duplicar veredito longo + mensagem)."""
    titulo = {
        Semaforo.VERDE: "Aprovado",
        Semaforo.AMARELO: "Atenção",
        Semaforo.VERMELHO: "Reprovado",
    }[decisao.semaforo]
    return titulo, decisao.mensagem


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
