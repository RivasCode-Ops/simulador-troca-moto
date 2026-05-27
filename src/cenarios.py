"""Cenários nomeados para comparação executiva."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .financiamento import ResultadoFinanciamento, financiamento_vazio, financiar_price


@dataclass(frozen=True)
class Premissas:
    valor_moto_usada: float = 25_000.0
    valor_moto_nova: float = 30_000.0
    entrada_comprador_usada: float = 20_000.0
    saldo_venda_financiado: float = 5_000.0
    entrada_loja_nova: float = 20_000.0
    saldo_compra_financiado: float = 10_000.0
    taxa_venda_mensal_pct: float = 2.0
    taxa_compra_mensal_pct: float = 2.0
    prazo_venda_meses: int = 24
    prazo_compra_meses: int = 36
    taxas_contrato_venda: float = 0.0
    taxas_contrato_compra: float = 500.0
    comprador_libera_saldo_na_hora: bool = True


@dataclass(frozen=True)
class ResultadoCenario:
    id: str
    nome: str
    descricao: str
    desembolso_vista_ideal: float
    total_juros: float
    total_parcelas_mensais: float
    custo_extra_vs_ideal: float
    parcela_venda: float | None
    parcela_compra: float | None
    fin_venda: ResultadoFinanciamento | None
    fin_compra: ResultadoFinanciamento | None
    total_desembolsado: float
    observacao: str
    destaque: bool = False


def premissas_from_inputs(
    valor_usada: float,
    valor_nova: float,
    entrada_comprador: float,
    entrada_loja: float,
    taxa_venda: float,
    taxa_compra: float,
    prazo_venda: int,
    prazo_compra: int,
    taxas_venda: float,
    taxas_compra: float,
    libera_saldo: bool,
) -> Premissas:
    return Premissas(
        valor_moto_usada=valor_usada,
        valor_moto_nova=valor_nova,
        entrada_comprador_usada=entrada_comprador,
        saldo_venda_financiado=max(0.0, valor_usada - entrada_comprador),
        entrada_loja_nova=entrada_loja,
        saldo_compra_financiado=max(0.0, valor_nova - entrada_loja),
        taxa_venda_mensal_pct=taxa_venda,
        taxa_compra_mensal_pct=taxa_compra,
        prazo_venda_meses=prazo_venda,
        prazo_compra_meses=prazo_compra,
        taxas_contrato_venda=taxas_venda,
        taxas_contrato_compra=taxas_compra,
        comprador_libera_saldo_na_hora=libera_saldo,
    )


def _custo_extra(desembolso_imediato: float, total_pago_financiamentos: float, desembolso_ideal: float) -> float:
    return round(desembolso_imediato + total_pago_financiamentos - desembolso_ideal, 2)


def _simular_plano(p: Premissas, nome: str, descricao: str, cid: str, destaque: bool = False) -> ResultadoCenario:
    fin_venda = (
        financiar_price(p.saldo_venda_financiado, p.taxa_venda_mensal_pct, p.prazo_venda_meses, p.taxas_contrato_venda)
        if p.saldo_venda_financiado > 0
        else None
    )
    if p.saldo_compra_financiado > 0:
        fin_compra = financiar_price(
            p.saldo_compra_financiado,
            p.taxa_compra_mensal_pct,
            p.prazo_compra_meses,
            p.taxas_contrato_compra,
        )
    else:
        fin_compra = financiamento_vazio()
    gap_ideal = p.valor_moto_nova - p.valor_moto_usada

    if p.comprador_libera_saldo_na_hora:
        desembolso_vista = 0.0
        total_pago = fin_compra.total_pago
        juros = fin_compra.total_juros
        obs = "Saldo financiado liberado na assinatura."
    else:
        desembolso_vista = gap_ideal
        total_pago = (fin_venda.total_pago if fin_venda else 0) + fin_compra.total_pago
        juros = (fin_venda.total_juros if fin_venda else 0) + fin_compra.total_juros
        obs = "Você só recebe a entrada à vista até o comprador quitar o saldo."

    return ResultadoCenario(
        id=cid,
        nome=nome,
        descricao=descricao,
        desembolso_vista_ideal=desembolso_vista,
        total_juros=round(juros, 2),
        total_parcelas_mensais=fin_compra.valor_parcela,
        custo_extra_vs_ideal=_custo_extra(desembolso_vista, total_pago, gap_ideal),
        parcela_venda=fin_venda.valor_parcela if fin_venda else None,
        parcela_compra=fin_compra.valor_parcela,
        fin_venda=fin_venda,
        fin_compra=fin_compra,
        total_desembolsado=round(desembolso_vista + total_pago, 2),
        observacao=obs,
        destaque=destaque,
    )


def cenario_ideal(p: Premissas) -> ResultadoCenario:
    gap = p.valor_moto_nova - p.valor_moto_usada
    return ResultadoCenario(
        id="ideal",
        nome="Referência — troca ideal",
        descricao="Usada no valor de mercado + diferença à vista, sem juros.",
        desembolso_vista_ideal=gap,
        total_juros=0.0,
        total_parcelas_mensais=0.0,
        custo_extra_vs_ideal=0.0,
        parcela_venda=None,
        parcela_compra=None,
        fin_venda=None,
        fin_compra=None,
        total_desembolsado=gap,
        observacao=f"Exige {gap:,.0f} em caixa hoje.".replace(",", "."),
    )


def cenario_esperar_juntar(p: Premissas) -> ResultadoCenario:
    gap = p.valor_moto_nova - p.valor_moto_usada
    meses_sugestao = max(1, int(gap / 500))  # ilustrativo: R$ 500/mês
    return ResultadoCenario(
        id="esperar",
        nome="Esperar e juntar mais",
        descricao="Adiar a troca até ter a diferença à vista (sem financiar a operação).",
        desembolso_vista_ideal=gap,
        total_juros=0.0,
        total_parcelas_mensais=0.0,
        custo_extra_vs_ideal=0.0,
        parcela_venda=None,
        parcela_compra=None,
        fin_venda=None,
        fin_compra=None,
        total_desembolsado=gap,
        observacao=(
            f"Meta: juntar {gap:,.0f} antes de trocar. "
            f"Exemplo: ~{meses_sugestao} meses guardando R$ 500/mês (ajuste ao seu orçamento)."
        ).replace(",", "."),
    )


def cenario_venda_vista(p: Premissas) -> ResultadoCenario:
    saldo = p.valor_moto_nova - p.valor_moto_usada
    fin_compra = financiar_price(saldo, p.taxa_compra_mensal_pct, p.prazo_compra_meses, p.taxas_contrato_compra)
    gap = saldo
    return ResultadoCenario(
        id="vista_um_fin",
        nome="Venda à vista + 1 financiamento",
        descricao="Comprador paga o valor integral da usada; você financia só a diferença da nova.",
        desembolso_vista_ideal=0.0,
        total_juros=fin_compra.total_juros,
        total_parcelas_mensais=fin_compra.valor_parcela,
        custo_extra_vs_ideal=_custo_extra(0.0, fin_compra.total_pago, gap),
        parcela_venda=None,
        parcela_compra=fin_compra.valor_parcela,
        fin_venda=None,
        fin_compra=fin_compra,
        total_desembolsado=fin_compra.total_pago,
        observacao="Comprador precisa de 25k à vista ou financiamento total no banco dele.",
    )


def listar_cenarios(p: Premissas) -> list[ResultadoCenario]:
    """Cenários executivos nomeados para o dashboard."""
    plano = _simular_plano(
        p,
        nome="Plano atual",
        descricao="Configuração que você definiu na sidebar (venda + compra financiadas).",
        cid="plano_atual",
        destaque=True,
    )

    extra = 5_000.0 if p.entrada_comprador_usada + 5_000 <= p.valor_moto_usada else 2_000.0
    p_mais = replace(
        p,
        entrada_comprador_usada=p.entrada_comprador_usada + extra,
        entrada_loja_nova=p.entrada_loja_nova + extra,
        saldo_venda_financiado=max(0.0, p.valor_moto_usada - (p.entrada_comprador_usada + extra)),
        saldo_compra_financiado=max(0.0, p.valor_moto_nova - (p.entrada_loja_nova + extra)),
    )
    mais_entrada = _simular_plano(
        p_mais,
        nome="Mais entrada",
        descricao=f"Comprador entra com +R$ {extra:,.0f} à vista; menos financiado na nova.".replace(",", "."),
        cid="mais_entrada",
    )

    prazo_menor = min(24, p.prazo_compra_meses) if p.prazo_compra_meses > 24 else p.prazo_compra_meses
    p_prazo = replace(p, prazo_compra_meses=prazo_menor)
    menor_prazo = _simular_plano(
        p_prazo,
        nome="Menor prazo",
        descricao=f"Prazo da moto nova em {prazo_menor} meses (menos juros, parcela maior).",
        cid="menor_prazo",
    )

    return [
        cenario_ideal(p),
        plano,
        mais_entrada,
        menor_prazo,
        cenario_venda_vista(p),
        cenario_esperar_juntar(p),
    ]


def cenarios_para_exportacao(cenarios: list[ResultadoCenario]) -> list[dict]:
    return [
        {
            "id": c.id,
            "cenario": c.nome,
            "descricao": c.descricao,
            "a_vista_agora": c.desembolso_vista_ideal,
            "total_desembolsado": c.total_desembolsado,
            "parcela_moto_nova": c.parcela_compra or 0,
            "parcela_comprador": c.parcela_venda or 0,
            "juros_totais": c.total_juros,
            "custo_extra_vs_ideal": c.custo_extra_vs_ideal,
            "observacao": c.observacao,
        }
        for c in cenarios
    ]
