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
    cet_aproximado: float
    tabela: list[dict]


def taxa_anual_para_mensal(taxa_anual_pct: float) -> float:
    return (1 + taxa_anual_pct / 100) ** (1 / 12) - 1


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
    cet = (total_pago / pv - 1) * 100 if pv > 0 else 0.0
    return ResultadoFinanciamento(
        valor_financiado=pv,
        taxa_mensal=taxa,
        parcelas=parcelas,
        valor_parcela=round(pmt, 2),
        total_pago=round(total_pago, 2),
        total_juros=round(total_juros, 2),
        cet_aproximado=round(cet, 2),
        tabela=tabela,
    )
