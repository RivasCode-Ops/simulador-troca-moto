"""Montagem do relatório executivo da simulação (tela e exportação futura)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .decisao import (
    ExplicacaoCustoExtra,
    LimitesDecisao,
    ResultadoDecisao,
    peso_exibicao_pct,
    peso_total_ativo,
)
from .fipe_analise import AnaliseFipeVenda
from .operacao import DadosOperacao, ResultadoTroca
from .ui import _TITULO_BANNER, brl, mensagem_banner_resumo, pct


@dataclass(frozen=True)
class LinhaRelatorio:
    rotulo: str
    valor: str


@dataclass(frozen=True)
class CriterioRelatorio:
    nome: str
    status: str
    peso_pct: str
    uso_limite: str
    mensagem: str


@dataclass(frozen=True)
class RelatorioSimulacao:
    identificacao: str
    gerado_em: str
    gerado_em_iso: str
    resumo_executivo: str
    decisao_titulo: str
    semaforo: str
    veredito: str
    pontuacao_risco: float
    kpis: tuple[LinhaRelatorio, ...]
    venda: tuple[LinhaRelatorio, ...]
    compra: tuple[LinhaRelatorio, ...]
    fipe: tuple[LinhaRelatorio, ...] | None
    custo_extra: tuple[LinhaRelatorio, ...]
    criterios: tuple[CriterioRelatorio, ...]
    limites_h: tuple[LinhaRelatorio, ...]
    recomendacoes: tuple[str, ...]
    avisos: tuple[str, ...] = field(default_factory=tuple)

    def para_dict(self) -> dict[str, Any]:
        return asdict(self)

    def para_markdown(self) -> str:
        """Texto único do relatório (base para exportação PDF futura)."""
        linhas = [
            f"# Relatório da simulação — {self.identificacao}",
            f"*{self.gerado_em}*",
            "",
            "## Resumo executivo",
            self.resumo_executivo,
            "",
            f"**{self.decisao_titulo}** · {self.veredito} · Risco {self.pontuacao_risco:.0f}/100",
            "",
            "## KPIs principais",
        ]
        for item in self.kpis:
            linhas.append(f"- **{item.rotulo}:** {item.valor}")
        linhas.extend(["", "## Venda da usada"])
        for item in self.venda:
            linhas.append(f"- {item.rotulo}: {item.valor}")
        linhas.extend(["", "## Compra da nova"])
        for item in self.compra:
            linhas.append(f"- {item.rotulo}: {item.valor}")
        linhas.extend(["", "## FIPE"])
        if self.fipe:
            for item in self.fipe:
                linhas.append(f"- {item.rotulo}: {item.valor}")
        else:
            linhas.append("- Consulta FIPE não realizada nesta sessão.")
        linhas.extend(["", "## Custo extra da troca"])
        for item in self.custo_extra:
            linhas.append(f"- {item.rotulo}: {item.valor}")
        if self.criterios:
            linhas.extend(["", "## Critérios (seção H)"])
            for c in self.criterios:
                linhas.append(
                    f"- **{c.nome}** ({c.status}, peso {c.peso_pct}, {c.uso_limite}): {c.mensagem}"
                )
        if self.limites_h:
            linhas.extend(["", "## Limites configurados"])
            for item in self.limites_h:
                linhas.append(f"- {item.rotulo}: {item.valor}")
        if self.recomendacoes:
            linhas.extend(["", "## Recomendações"])
            for r in self.recomendacoes:
                linhas.append(f"- {r}")
        if self.avisos:
            linhas.extend(["", "## Avisos da operação"])
            for a in self.avisos:
                linhas.append(f"- {a}")
        return "\n".join(linhas)


def _agora_local() -> tuple[str, str]:
    agora = datetime.now()
    return agora.strftime("%d/%m/%Y %H:%M"), agora.isoformat(timespec="seconds")


def _linhas_fipe(fipe: AnaliseFipeVenda | dict[str, Any]) -> tuple[LinhaRelatorio, ...]:
    if isinstance(fipe, dict):
        pf = float(fipe.get("preco_fipe", 0))
        pv = float(fipe.get("preco_venda", 0))
        diff = float(fipe.get("diferenca_reais", pv - pf))
        diff_pct = float(fipe.get("diferenca_pct", 0))
        cob = fipe.get("cobertura_custo_extra_pct")
        marca = fipe.get("marca", "—")
        modelo = fipe.get("modelo", "—")
        ref = fipe.get("mes_referencia", "—")
        codigo = fipe.get("codigo_fipe", "—")
    else:
        pf = fipe.preco_fipe
        pv = fipe.preco_venda
        diff = fipe.diferenca_reais
        diff_pct = fipe.diferenca_pct
        cob = fipe.cobertura_custo_extra_pct
        marca = fipe.marca
        modelo = fipe.modelo
        ref = fipe.mes_referencia
        codigo = fipe.codigo_fipe

    linhas = [
        LinhaRelatorio("Veículo", f"{marca} · {modelo}"),
        LinhaRelatorio("Referência FIPE", ref),
        LinhaRelatorio("Código FIPE", str(codigo)),
        LinhaRelatorio("Preço FIPE", brl(pf)),
        LinhaRelatorio("Preço alvo (usada)", brl(pv)),
        LinhaRelatorio("Diferença", f"{brl(diff)} ({diff_pct:+.1f}%)"),
    ]
    if cob is not None:
        linhas.append(LinhaRelatorio("Cobre custo extra", f"{float(cob):.0f}%"))
    return tuple(linhas)


def _recomendacoes(
    decisao: ResultadoDecisao,
    troca: ResultadoTroca,
) -> tuple[str, ...]:
    if decisao.resumo_acoes:
        base = list(decisao.resumo_acoes)
    elif decisao.semaforo.value == "verde":
        base = [
            "Documente esta proposta e compare com pelo menos um cenário alternativo salvo no histórico.",
            "Confirme na financeira a taxa efetiva e as condições de liberação do saldo financiado.",
        ]
    elif decisao.semaforo.value == "amarelo":
        base = [
            "Renegocie custo extra, parcela ou prazo antes de fechar — a operação está no limite.",
            "Simule mais entrada na nova ou na usada e salve a versão renegociada para comparar.",
        ]
    else:
        base = [
            "Não feche nestes termos — ajuste custo extra, parcela ou entradas até o semáforo melhorar.",
            "Use os cenários da seção 4 para testar mais entrada ou prazo menor.",
        ]
    if decisao.motivos_falha and decisao.resumo_acoes:
        pass
    elif decisao.motivos_falha:
        base.insert(0, decisao.motivos_falha[0])
    return tuple(dict.fromkeys(base))[:5]


def montar_relatorio(
    *,
    dados: DadosOperacao,
    troca: ResultadoTroca,
    decisao: ResultadoDecisao,
    limites: LimitesDecisao,
    explicacao: ExplicacaoCustoExtra,
    fipe: AnaliseFipeVenda | dict[str, Any] | None = None,
    nome_cenario: str = "Simulação atual",
) -> RelatorioSimulacao:
    gerado_em, gerado_em_iso = _agora_local()
    d = dados
    v = troca.venda
    cp = troca.compra
    fin = cp.financiamento

    identificacao = (
        f"{nome_cenario} · usada {brl(d.valor_moto_usada)} → nova {brl(d.valor_moto_nova)}"
    )
    titulo = _TITULO_BANNER[decisao.semaforo]
    msg = mensagem_banner_resumo(decisao)
    resumo = f"{msg} Custo extra de {brl(troca.custo_extra_vs_ideal)} frente à troca ideal."

    kpis = (
        LinhaRelatorio("Custo extra", brl(troca.custo_extra_vs_ideal)),
        LinhaRelatorio("Parcela moto nova", brl(cp.parcela_moto_nova)),
        LinhaRelatorio("Total a receber (usada)", brl(v.total_recebido_pelo_vendedor)),
        LinhaRelatorio("Score de risco", f"{decisao.pontuacao_risco:.0f}/100"),
    )

    venda = (
        LinhaRelatorio("Valor da usada", brl(d.valor_moto_usada)),
        LinhaRelatorio("Entrada do comprador", brl(d.entrada_comprador)),
        LinhaRelatorio("Saldo financiado (comprador)", brl(v.saldo_financiado)),
        LinhaRelatorio("Parcela do comprador", brl(v.parcela_comprador)),
        LinhaRelatorio("Total que você recebe", brl(v.total_recebido_pelo_vendedor)),
        LinhaRelatorio(
            "Prazo do saldo",
            "Imediato" if v.prazo_recebimento_saldo_meses == 0 else f"{v.prazo_recebimento_saldo_meses} mês(es)",
        ),
        LinhaRelatorio("Juros embutidos (comprador)", brl(v.juros_embutidos_comprador)),
    )

    compra = (
        LinhaRelatorio("Valor da nova", brl(d.valor_moto_nova)),
        LinhaRelatorio("Entrada na loja", brl(d.entrada_loja)),
        LinhaRelatorio("Principal financiado", brl(cp.valor_financiado_principal)),
        LinhaRelatorio("Parcela", brl(cp.parcela_moto_nova)),
        LinhaRelatorio("Total pago ao banco", brl(cp.total_pago_banco)),
        LinhaRelatorio("Juros totais", brl(cp.juros_totais)),
        LinhaRelatorio("Juros", f"{pct(fin.taxa_mensal * 100)} ao mês"),
        LinhaRelatorio("Taxa nominal a.a.", pct(fin.taxa_nominal_anual_pct)),
        LinhaRelatorio("Taxa efetiva a.a. (calc.)", pct(fin.taxa_efetiva_anual_pct)),
        LinhaRelatorio(
            "Taxa informada",
            pct(cp.cet_informado_pct) if cp.cet_informado_pct else "—",
        ),
    )

    custo_extra = (
        LinhaRelatorio("Troca ideal (só diferença)", brl(explicacao.troca_ideal)),
        LinhaRelatorio("À vista agora", brl(explicacao.desembolso_vista_agora)),
        LinhaRelatorio("Total das parcelas", brl(explicacao.total_parcelas_financiamentos)),
        LinhaRelatorio("Total da operação", brl(explicacao.total_operacao)),
        LinhaRelatorio("Custo extra", brl(explicacao.custo_extra)),
    )
    if decisao.pct_custo_extra_do_limite is not None and limites.usar_limites:
        custo_extra = custo_extra + (
            LinhaRelatorio(
                "Uso do limite (custo extra)",
                f"{decisao.pct_custo_extra_do_limite:.0f}% de {brl(limites.custo_extra_maximo)}",
            ),
        )

    criterios: list[CriterioRelatorio] = []
    if limites.usar_limites and decisao.criterios:
        peso_total = peso_total_ativo(decisao.criterios)
        for c in decisao.criterios:
            if c.peso <= 0 and c.id == "risco_caixa":
                peso_txt = "—"
            elif c.peso > 0:
                peso_txt = f"{peso_exibicao_pct(c, peso_total):.0f}%"
            else:
                peso_txt = "—"
            criterios.append(
                CriterioRelatorio(
                    nome=c.nome,
                    status=c.status_label,
                    peso_pct=peso_txt,
                    uso_limite=f"{c.pct_do_limite:.0f}%",
                    mensagem=c.mensagem,
                )
            )

    limites_h: list[LinhaRelatorio] = []
    if limites.usar_limites:
        limites_h = [
            LinhaRelatorio("Custo extra máximo", brl(limites.custo_extra_maximo)),
            LinhaRelatorio("Parcela máxima (nova)", brl(limites.parcela_maxima_nova)),
            LinhaRelatorio(
                "Prazo máx. saldo financ.",
                "Imediato" if limites.prazo_max_receber_saldo_meses == 0 else f"{limites.prazo_max_receber_saldo_meses} m",
            ),
            LinhaRelatorio("Entrada mín. comprador", brl(limites.entrada_minima_comprador)),
        ]
        if limites.cet_maximo_tolerado_pct is not None:
            limites_h.append(
                LinhaRelatorio(
                    "Taxa efetiva máx. a.a.",
                    pct(limites.cet_maximo_tolerado_pct),
                )
            )
    else:
        limites_h = [LinhaRelatorio("Semáforo", "Limites desativados na sidebar")]

    return RelatorioSimulacao(
        identificacao=identificacao,
        gerado_em=gerado_em,
        gerado_em_iso=gerado_em_iso,
        resumo_executivo=resumo,
        decisao_titulo=titulo,
        semaforo=decisao.semaforo.value,
        veredito=decisao.veredito.value,
        pontuacao_risco=decisao.pontuacao_risco,
        kpis=kpis,
        venda=venda,
        compra=compra,
        fipe=_linhas_fipe(fipe) if fipe else None,
        custo_extra=custo_extra,
        criterios=tuple(criterios),
        limites_h=tuple(limites_h),
        recomendacoes=_recomendacoes(decisao, troca),
        avisos=tuple(troca.avisos),
    )
