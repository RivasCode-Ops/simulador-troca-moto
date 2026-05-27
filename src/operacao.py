"""Simulação unificada da operação de troca (venda + compra)."""

from __future__ import annotations

from dataclasses import dataclass

from .financiamento import ResultadoFinanciamento, financiamento_vazio, financiar_price


@dataclass(frozen=True)
class DadosOperacao:
    valor_moto_usada: float = 25_000.0
    valor_moto_nova: float = 30_000.0
    entrada_comprador: float = 20_000.0
    entrada_loja: float = 20_000.0
    taxa_venda_mensal_pct: float = 2.0
    prazo_venda_meses: int = 24
    taxa_compra_mensal_pct: float = 2.0
    prazo_compra_meses: int = 36
    taxas_contrato_venda: float = 0.0
    taxas_contrato_compra: float = 500.0
    comprador_libera_saldo_na_hora: bool = True
    cet_compra_informado_pct: float | None = None


@dataclass(frozen=True)
class LadoVenda:
    entrada_vista: float
    saldo_financiado: float
    financiamento: ResultadoFinanciamento | None
    parcela_comprador: float
    total_recebido_pelo_vendedor: float
    juros_embutidos_comprador: float
    prazo_recebimento_saldo_meses: int
    observacao_recebimento: str


@dataclass(frozen=True)
class LadoCompra:
    entrada_loja: float
    valor_financiado_principal: float
    financiamento: ResultadoFinanciamento
    parcela_moto_nova: float
    total_pago_banco: float
    juros_totais: float
    cet_calculado_pct: float
    cet_informado_pct: float | None


@dataclass(frozen=True)
class TrocaIdeal:
    diferenca_a_vista: float
    total_desembolso: float
    descricao: str


@dataclass(frozen=True)
class ResultadoTroca:
    dados: DadosOperacao
    venda: LadoVenda
    compra: LadoCompra
    ideal: TrocaIdeal
    desembolso_vista_agora: float
    total_desembolsado_operacao: float
    custo_extra_vs_ideal: float
    juros_pagos_compra: float
    juros_embutidos_venda_comprador: float
    saldo_liquido_juros: float
    juros_total_seu_bolso: float
    avisos: tuple[str, ...] = ()


def _coletar_avisos(d: DadosOperacao, saldo_venda: float, saldo_compra: float) -> tuple[str, ...]:
    msgs: list[str] = []
    if d.entrada_comprador > d.valor_moto_usada:
        msgs.append(
            "Comprador paga mais que o valor da moto usada — não há saldo a financiar para o comprador."
        )
    elif d.entrada_comprador == d.valor_moto_usada and d.valor_moto_usada > 0:
        msgs.append("Entrada do comprador igual ao valor da usada — saldo financiado do comprador será zero.")

    if d.entrada_loja > d.valor_moto_nova:
        msgs.append(
            "Entrada na loja maior que o valor da moto nova — financiamento da compra será zero."
        )
    elif d.entrada_loja == d.valor_moto_nova and d.valor_moto_nova > 0:
        msgs.append("Entrada na loja igual ao valor da moto nova — financiamento da compra será zero.")

    return tuple(msgs)


def _financiar_se_positivo(
    valor: float,
    taxa_pct: float,
    prazo: int,
    taxas: float,
) -> ResultadoFinanciamento | None:
    if valor <= 0:
        return None
    return financiar_price(valor, taxa_pct, prazo, taxas)


def simular_troca(d: DadosOperacao) -> ResultadoTroca:
    saldo_venda = max(0.0, d.valor_moto_usada - d.entrada_comprador)
    saldo_compra = max(0.0, d.valor_moto_nova - d.entrada_loja)
    gap_ideal = d.valor_moto_nova - d.valor_moto_usada

    fin_venda = _financiar_se_positivo(
        saldo_venda,
        d.taxa_venda_mensal_pct,
        d.prazo_venda_meses,
        d.taxas_contrato_venda,
    )
    fin_compra = _financiar_se_positivo(
        saldo_compra,
        d.taxa_compra_mensal_pct,
        d.prazo_compra_meses,
        d.taxas_contrato_compra,
    )
    if fin_compra is None:
        fin_compra = financiamento_vazio()

    avisos = _coletar_avisos(d, saldo_venda, saldo_compra)

    if d.comprador_libera_saldo_na_hora:
        total_recebido = d.entrada_comprador + saldo_venda
        prazo_receb = 0
        obs_rec = "Financeira libera o saldo financiado na assinatura (você recebe o valor da usada na hora)."
        desembolso_vista = 0.0
        total_pago_fin = fin_compra.total_pago
    else:
        total_recebido = d.entrada_comprador + (fin_venda.total_pago if fin_venda else 0)
        prazo_receb = d.prazo_venda_meses
        obs_rec = (
            f"Você recebe R$ {d.entrada_comprador:,.2f} agora; "
            f"saldo entra em {d.prazo_venda_meses} parcelas do comprador."
        ).replace(",", "X").replace(".", ",").replace("X", ".")
        desembolso_vista = gap_ideal
        total_pago_fin = (fin_venda.total_pago if fin_venda else 0) + fin_compra.total_pago

    venda = LadoVenda(
        entrada_vista=d.entrada_comprador,
        saldo_financiado=saldo_venda,
        financiamento=fin_venda,
        parcela_comprador=fin_venda.valor_parcela if fin_venda else 0.0,
        total_recebido_pelo_vendedor=round(total_recebido, 2),
        juros_embutidos_comprador=fin_venda.total_juros if fin_venda else 0.0,
        prazo_recebimento_saldo_meses=prazo_receb,
        observacao_recebimento=obs_rec,
    )

    compra = LadoCompra(
        entrada_loja=d.entrada_loja,
        valor_financiado_principal=saldo_compra,
        financiamento=fin_compra,
        parcela_moto_nova=fin_compra.valor_parcela,
        total_pago_banco=fin_compra.total_pago,
        juros_totais=fin_compra.total_juros,
        cet_calculado_pct=fin_compra.cet_aproximado,
        cet_informado_pct=d.cet_compra_informado_pct,
    )

    total_desembolsado = round(desembolso_vista + total_pago_fin, 2)
    custo_extra = round(total_desembolsado - gap_ideal, 2)

    juros_pagos = fin_compra.total_juros
    if not d.comprador_libera_saldo_na_hora and fin_venda:
        juros_pagos += fin_venda.total_juros

    return ResultadoTroca(
        dados=d,
        venda=venda,
        compra=compra,
        ideal=TrocaIdeal(
            diferenca_a_vista=gap_ideal,
            total_desembolso=gap_ideal,
            descricao="Troca na concessionária: usada no valor de mercado + diferença à vista, sem juros.",
        ),
        desembolso_vista_agora=desembolso_vista,
        total_desembolsado_operacao=total_desembolsado,
        custo_extra_vs_ideal=custo_extra,
        juros_pagos_compra=fin_compra.total_juros,
        juros_embutidos_venda_comprador=fin_venda.total_juros if fin_venda else 0.0,
        saldo_liquido_juros=round(
            juros_pagos - (0.0 if d.comprador_libera_saldo_na_hora else (fin_venda.total_juros if fin_venda else 0)),
            2,
        ),
        juros_total_seu_bolso=round(juros_pagos, 2),
        avisos=avisos,
    )
