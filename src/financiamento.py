"""Cálculos de financiamento (Tabela Price e SAC)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoFinanciamento:
    valor_financiado: float
    taxa_mensal: float
    parcelas: int
    valor_parcela: float
    total_pago: float
    total_juros: float
    taxa_nominal_anual_pct: float
    taxa_efetiva_anual_pct: float
    custo_total_prazo_pct: float
    cet_aproximado: float  # alias: taxa_efetiva_anual_pct (compat.)
    tabela: list[dict]


def taxa_anual_para_mensal(taxa_anual_pct: float) -> float:
    return (1 + taxa_anual_pct / 100) ** (1 / 12) - 1


def taxa_nominal_anual_pct(taxa_mensal: float) -> float:
    """APR nominal linear: taxa mensal × 12 (em % a.a.)."""
    return round(taxa_mensal * 12 * 100, 4)


def taxa_efetiva_anual_pct(taxa_mensal: float) -> float:
    """Taxa efetiva anual composta: (1 + i_m)^12 − 1 (em % a.a.)."""
    if taxa_mensal <= 0:
        return 0.0
    return round(((1 + taxa_mensal) ** 12 - 1) * 100, 2)


def custo_total_prazo_pct(valor_presente: float, total_pago: float) -> float:
    """Custo total do contrato no prazo vs PV (não é CET regulatório)."""
    if valor_presente <= 0:
        return 0.0
    return round((total_pago / valor_presente - 1) * 100, 2)


def parcela_price(pv: float, taxa_mensal: float, n: int) -> float:
    if n <= 0:
        raise ValueError("Número de parcelas deve ser positivo.")
    if pv <= 0:
        return 0.0
    if taxa_mensal == 0:
        return pv / n
    fator = (1 + taxa_mensal) ** n
    return pv * (taxa_mensal * fator) / (fator - 1)


def tabela_price(pv: float, taxa_mensal: float, n: int) -> list[dict]:
    pmt = parcela_price(pv, taxa_mensal, n)
    saldo = pv
    linhas: list[dict] = []
    for k in range(1, n + 1):
        juros = saldo * taxa_mensal
        amort = pmt - juros
        saldo = max(0.0, saldo - amort)
        linhas.append(
            {
                "parcela": k,
                "pagamento": round(pmt, 2),
                "juros": round(juros, 2),
                "amortizacao": round(amort, 2),
                "saldo": round(saldo, 2),
            }
        )
    return linhas


def financiamento_vazio() -> ResultadoFinanciamento:
    """Financiamento inexistente (saldo zero) — sem parcela fantasma."""
    return ResultadoFinanciamento(
        valor_financiado=0.0,
        taxa_mensal=0.0,
        parcelas=0,
        valor_parcela=0.0,
        total_pago=0.0,
        total_juros=0.0,
        taxa_nominal_anual_pct=0.0,
        taxa_efetiva_anual_pct=0.0,
        custo_total_prazo_pct=0.0,
        cet_aproximado=0.0,
        tabela=[],
    )


def financiar_price(
    valor_financiado: float,
    taxa_mensal_pct: float,
    parcelas: int,
    taxas_contrato: float = 0.0,
) -> ResultadoFinanciamento:
    """taxa_mensal_pct: ex. 2.0 para 2% ao mês."""
    taxa = taxa_mensal_pct / 100
    pv = valor_financiado + taxas_contrato
    pmt = parcela_price(pv, taxa, parcelas)
    tabela = tabela_price(pv, taxa, parcelas)
    total_pago = sum(l["pagamento"] for l in tabela)
    total_juros = total_pago - pv
    nominal_aa = taxa_nominal_anual_pct(taxa)
    efetiva_aa = taxa_efetiva_anual_pct(taxa)
    custo_prazo = custo_total_prazo_pct(pv, total_pago)
    return ResultadoFinanciamento(
        valor_financiado=pv,
        taxa_mensal=taxa,
        parcelas=parcelas,
        valor_parcela=round(pmt, 2),
        total_pago=round(total_pago, 2),
        total_juros=round(total_juros, 2),
        taxa_nominal_anual_pct=nominal_aa,
        taxa_efetiva_anual_pct=efetiva_aa,
        custo_total_prazo_pct=custo_prazo,
        cet_aproximado=efetiva_aa,
        tabela=tabela,
    )
