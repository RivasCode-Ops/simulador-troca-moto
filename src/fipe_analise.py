"""Comparação entre preço FIPE e venda pretendida."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .fipe import FipePreco


@dataclass(frozen=True)
class AnaliseFipeVenda:
    preco_fipe: float
    preco_venda: float
    codigo_fipe: str
    marca: str
    modelo: str
    ano_modelo: int
    combustivel: str
    mes_referencia: str
    diferenca_reais: float
    diferenca_pct: float
    acima_da_fipe: bool
    cobertura_custo_extra_pct: float | None
    perda_apos_fipe: float | None

    def para_dict(self) -> dict:
        return asdict(self)

    @property
    def rotulo_diferenca(self) -> str:
        if self.diferenca_reais > 0:
            return f"{self.diferenca_pct:+.1f}% acima da FIPE"
        if self.diferenca_reais < 0:
            return f"{abs(self.diferenca_pct):.1f}% abaixo da FIPE"
        return "igual à FIPE"


def analisar_fipe_vs_venda(
    fipe: FipePreco,
    preco_venda: float,
    custo_extra_troca: float,
) -> AnaliseFipeVenda:
    diff = round(preco_venda - fipe.valor, 2)
    if fipe.valor > 0:
        diff_pct = round((preco_venda / fipe.valor - 1) * 100, 2)
    else:
        diff_pct = 0.0

    folga = max(0.0, diff)
    if custo_extra_troca > 0 and folga > 0:
        cobertura = round(min(100.0, (folga / custo_extra_troca) * 100), 1)
        perda = round(max(0.0, custo_extra_troca - folga), 2)
    elif custo_extra_troca > 0:
        cobertura = 0.0
        perda = round(custo_extra_troca, 2)
    else:
        cobertura = None
        perda = None

    return AnaliseFipeVenda(
        preco_fipe=fipe.valor,
        preco_venda=preco_venda,
        codigo_fipe=fipe.codigo_fipe,
        marca=fipe.marca,
        modelo=fipe.modelo,
        ano_modelo=fipe.ano_modelo,
        combustivel=fipe.combustivel,
        mes_referencia=fipe.mes_referencia,
        diferenca_reais=diff,
        diferenca_pct=diff_pct,
        acima_da_fipe=diff > 0,
        cobertura_custo_extra_pct=cobertura,
        perda_apos_fipe=perda,
    )
