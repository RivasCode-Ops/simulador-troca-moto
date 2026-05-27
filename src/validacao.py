"""Validação de domínio dos parâmetros da simulação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelAviso = Literal["erro", "aviso", "info"]

TAXA_MENSAL_MIN = 0.0
TAXA_MENSAL_MAX = 5.0
TAXA_MENSAL_AVISO_ALTO = 4.0
PRAZOS_VALIDOS = (12, 18, 24, 36, 48)


@dataclass(frozen=True)
class AvisoValidacao:
    nivel: NivelAviso
    mensagem: str


def validar_entradas(
    valor_usada: float,
    valor_nova: float,
    entrada_comprador: float,
    entrada_loja: float,
    taxa_venda: float,
    taxa_compra: float,
    prazo_venda: int,
    prazo_compra: int,
) -> list[AvisoValidacao]:
    avisos: list[AvisoValidacao] = []

    if valor_usada <= 0:
        avisos.append(AvisoValidacao("erro", "Informe valor da moto usada maior que zero."))
    if valor_nova <= 0:
        avisos.append(AvisoValidacao("erro", "Informe valor da moto nova maior que zero."))
    if entrada_comprador < 0:
        avisos.append(AvisoValidacao("erro", "Entrada do comprador não pode ser negativa."))
    if entrada_loja < 0:
        avisos.append(AvisoValidacao("erro", "Entrada na loja não pode ser negativa."))

    for taxa, rotulo in ((taxa_venda, "comprador"), (taxa_compra, "moto nova")):
        if taxa < TAXA_MENSAL_MIN or taxa > TAXA_MENSAL_MAX:
            avisos.append(
                AvisoValidacao(
                    "erro",
                    f"Juros do {rotulo} fora da faixa ({TAXA_MENSAL_MIN:g}%–{TAXA_MENSAL_MAX:g}% a.m.).",
                )
            )
        elif taxa >= TAXA_MENSAL_AVISO_ALTO:
            avisos.append(
                AvisoValidacao(
                    "aviso",
                    f"Juros do {rotulo} em {taxa:.1f}% a.m. — taxa alta; confira na financeira.",
                )
            )

    for prazo, rotulo in ((prazo_venda, "comprador"), (prazo_compra, "moto nova")):
        if prazo not in PRAZOS_VALIDOS:
            avisos.append(
                AvisoValidacao(
                    "erro",
                    f"Prazo do {rotulo} ({prazo} meses) fora das opções suportadas.",
                )
            )

    if valor_usada > 0 and valor_nova > 0 and valor_nova < valor_usada:
        avisos.append(
            AvisoValidacao(
                "aviso",
                "Moto nova abaixo da usada — conferir se os valores estão corretos.",
            )
        )

    if valor_usada > 0 and entrada_comprador > valor_usada:
        avisos.append(
            AvisoValidacao(
                "aviso",
                "Entrada do comprador acima da usada — saldo financiado do comprador será zero.",
            )
        )
    elif valor_usada > 0 and entrada_comprador == valor_usada:
        avisos.append(
            AvisoValidacao("info", "Entrada do comprador cobre 100% da usada — sem saldo a financiar.")
        )

    if valor_nova > 0 and entrada_loja > valor_nova:
        avisos.append(
            AvisoValidacao(
                "aviso",
                "Entrada na loja acima do valor da moto nova — financiamento da compra será zero.",
            )
        )
    elif valor_nova > 0 and entrada_loja == valor_nova:
        avisos.append(
            AvisoValidacao("info", "Entrada na loja cobre 100% da moto nova — financiamento zero.")
        )

    return avisos


def tem_erro_bloqueante(avisos: list[AvisoValidacao]) -> bool:
    return any(a.nivel == "erro" for a in avisos)
