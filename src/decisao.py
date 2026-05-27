"""Regras de decisão — seção H (semáforo com severidade e pesos)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .operacao import ResultadoTroca


class Semaforo(str, Enum):
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"


class Severidade(str, Enum):
    OK = "ok"
    ATENCAO = "atencao"
    CRITICO = "critico"


class Veredito(str, Enum):
    ACEITAVEL = "Aceitável — dentro dos limites"
    CARO = "Caro — renegocie antes de fechar"
    REPROVADO = "Melhor esperar ou mudar o plano"
    INDEFINIDO = "Defina os limites de decisão"


@dataclass(frozen=True)
class LimitesDecisao:
    custo_extra_maximo: float = 4_000.0
    parcela_maxima_nova: float = 450.0
    prazo_max_receber_saldo_meses: int = 0
    cet_maximo_tolerado_pct: float | None = None
    entrada_minima_comprador: float = 20_000.0
    usar_limites: bool = True


PESOS = {
    "custo_extra": 35,
    "parcela": 30,
    "prazo_saldo": 20,
    "cet": 10,
    "entrada_comprador": 5,
}


@dataclass(frozen=True)
class CriterioDecisao:
    id: str
    nome: str
    peso: int
    valor_atual: float
    limite: float
    unidade: str
    pct_do_limite: float
    severidade: Severidade
    mensagem: str
    pontos_risco: float

    @property
    def status_label(self) -> str:
        return {"ok": "OK", "atencao": "Atenção", "critico": "Crítico"}[self.severidade.value]


@dataclass(frozen=True)
class ExplicacaoCustoExtra:
    troca_ideal: float
    desembolso_vista_agora: float
    total_parcelas_financiamentos: float
    total_operacao: float
    custo_extra: float
    formula_texto: str
    detalhe_linhas: list[str]


@dataclass(frozen=True)
class ResultadoDecisao:
    semaforo: Semaforo
    veredito: Veredito
    mensagem: str
    criterios: list[CriterioDecisao]
    pontuacao_risco: float
    custo_extra: float
    pct_custo_extra_do_limite: float | None
    motivos_falha: list[str]
    motivos_atencao: list[str]
    resumo_acoes: list[str]

    @property
    def checagens(self) -> list[CriterioDecisao]:
        return self.criterios


def explicar_custo_extra(troca: ResultadoTroca) -> ExplicacaoCustoExtra:
    ideal = troca.ideal.diferenca_a_vista
    vista = troca.desembolso_vista_agora
    parcelas = round(troca.total_desembolsado_operacao - vista, 2)
    total = troca.total_desembolsado_operacao
    extra = troca.custo_extra_vs_ideal
    linhas = [
        f"Troca ideal (só a diferença à vista): {ideal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"+ À vista agora (gap de caixa): {vista:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"+ Total das parcelas: {parcelas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"= Total da operação: {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"− Troca ideal: {ideal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"= Custo extra: {extra:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    ]
    return ExplicacaoCustoExtra(
        troca_ideal=ideal,
        desembolso_vista_agora=vista,
        total_parcelas_financiamentos=parcelas,
        total_operacao=total,
        custo_extra=extra,
        formula_texto="Custo extra = (À vista agora + Total das parcelas) − Troca ideal",
        detalhe_linhas=linhas,
    )


def _brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _criterio_teto(
    cid: str,
    nome: str,
    peso: int,
    valor: float,
    limite: float,
    unidade: str,
    ok: str,
    atencao: str,
    critico: str,
) -> CriterioDecisao:
    if cid == "custo_extra" and valor <= 0:
        return CriterioDecisao(
            id=cid,
            nome=nome,
            peso=peso,
            valor_atual=valor,
            limite=limite,
            unidade=unidade,
            pct_do_limite=0.0,
            severidade=Severidade.OK,
            mensagem=f"Custo extra {_brl(valor)} — abaixo do ideal (favorável).",
            pontos_risco=0.0,
        )
    pct = (valor / limite * 100) if limite > 0 else (100.0 if valor > 0 else 0.0)
    if valor > limite:
        sev, pts = Severidade.CRITICO, float(peso)
        msg = critico
    elif pct >= 70:
        sev, pts = Severidade.ATENCAO, peso * 0.5
        msg = atencao
    else:
        sev, pts = Severidade.OK, 0.0
        msg = ok
    return CriterioDecisao(
        id=cid,
        nome=nome,
        peso=peso,
        valor_atual=valor,
        limite=limite,
        unidade=unidade,
        pct_do_limite=round(pct, 1),
        severidade=sev,
        mensagem=msg,
        pontos_risco=pts,
    )


def _criterio_piso(cid: str, nome: str, peso: int, valor: float, limite: float, ok: str, atencao: str, critico: str) -> CriterioDecisao:
    pct = (valor / limite * 100) if limite > 0 else 100.0
    if valor < limite:
        sev, pts = Severidade.CRITICO, float(peso)
        msg = critico
    elif pct < 95:
        sev, pts = Severidade.ATENCAO, peso * 0.5
        msg = atencao
    else:
        sev, pts = Severidade.OK, 0.0
        msg = ok
    return CriterioDecisao(
        id=cid,
        nome=nome,
        peso=peso,
        valor_atual=valor,
        limite=limite,
        unidade="R$",
        pct_do_limite=round(pct, 1),
        severidade=sev,
        mensagem=msg,
        pontos_risco=pts,
    )


def _peso_total_ativo(criterios: list[CriterioDecisao]) -> float:
    return float(sum(c.peso for c in criterios if c.peso > 0))


def _pontuacao_normalizada(criterios: list[CriterioDecisao]) -> float:
    """Escala pontos brutos para 0–100 conforme pesos ativos (renormalização)."""
    total = _peso_total_ativo(criterios)
    if total <= 0:
        return 0.0
    bruto = sum(c.pontos_risco for c in criterios if c.peso > 0)
    return round(min(100.0, bruto / total * 100), 1)


def peso_total_ativo(criterios: list[CriterioDecisao]) -> float:
    return _peso_total_ativo(criterios)


def peso_exibicao_pct(criterio: CriterioDecisao, peso_total_ativo: float) -> float:
    if peso_total_ativo <= 0 or criterio.peso <= 0:
        return 0.0
    return round(criterio.peso / peso_total_ativo * 100, 1)


def _semaforo_final(criterios: list[CriterioDecisao], pontuacao: float) -> tuple[Semaforo, Veredito, str, list[str]]:
    criticos = [c for c in criterios if c.severidade == Severidade.CRITICO]
    atencoes = [c for c in criterios if c.severidade == Severidade.ATENCAO]
    ids = {c.id for c in criticos}

    acoes: list[str] = []
    for c in criticos + atencoes:
        if c.id == "custo_extra":
            acoes.append("Baixe juros/prazo ou aumente entrada do comprador para reduzir custo extra.")
        elif c.id == "parcela":
            acoes.append("Aumente entrada na nova ou reduza prazo se a parcela couber no orçamento.")
        elif c.id == "prazo_saldo":
            acoes.append("Exija liberação imediata do saldo financiado ou junte caixa para o gap.")
        elif c.id == "entrada_comprador":
            acoes.append("Negocie entrada mínima maior com o comprador da usada.")
        elif c.id == "taxa_efetiva":
            acoes.append("Compare taxa efetiva anual em outra financeira ou concessionária.")
        elif c.id == "risco_caixa":
            acoes.append("Adie a troca até cobrir a diferença à vista.")

    if criticos:
        sem, ver = Semaforo.VERMELHO, Veredito.REPROVADO
        if "custo_extra" in ids or "parcela" in ids:
            msg = "Custo extra ou parcela inviáveis — não feche sem renegociar."
        else:
            msg = f"{len(criticos)} critério(s) crítico(s) — revise antes de fechar."
    elif pontuacao >= 25 or atencoes:
        sem, ver = Semaforo.AMARELO, Veredito.CARO
        msg = (
            f"Risco {pontuacao:.0f}/100 — {len(atencoes)} alerta(s) intermediário(s). "
            "Negocie antes de assinar."
        )
    else:
        sem, ver = Semaforo.VERDE, Veredito.ACEITAVEL
        msg = (
            f"Dentro dos limites (risco {pontuacao:.0f}/100). "
            "Compare com cenários salvos no histórico."
        )

    return sem, ver, msg, list(dict.fromkeys(acoes))[:4]


def avaliar_decisao(troca: ResultadoTroca, limites: LimitesDecisao) -> ResultadoDecisao:
    ce = troca.custo_extra_vs_ideal
    if limites.custo_extra_maximo > 0:
        pct_ce = round(ce / limites.custo_extra_maximo * 100, 1)
        if pct_ce < 0:
            pct_ce = 0.0
    else:
        pct_ce = None

    if not limites.usar_limites:
        return ResultadoDecisao(
            semaforo=Semaforo.AMARELO,
            veredito=Veredito.INDEFINIDO,
            mensagem="Ative os limites de decisão para avaliar com semáforo.",
            criterios=[],
            pontuacao_risco=0.0,
            custo_extra=ce,
            pct_custo_extra_do_limite=pct_ce,
            motivos_falha=[],
            motivos_atencao=[],
            resumo_acoes=[],
        )

    par = troca.compra.parcela_moto_nova
    prazo = float(troca.venda.prazo_recebimento_saldo_meses)
    ent = troca.dados.entrada_comprador
    taxa_efetiva = troca.compra.cet_informado_pct or troca.compra.cet_calculado_pct

    criterios = [
        _criterio_teto(
            "custo_extra",
            "Custo extra",
            PESOS["custo_extra"],
            ce,
            limites.custo_extra_maximo,
            "R$",
            ok=f"Custo extra {_brl(ce)} dentro do teto {_brl(limites.custo_extra_maximo)}.",
            atencao=f"Custo extra {_brl(ce)} em {pct_ce or 0:.0f}% do limite — margem apertada.",
            critico=f"Custo extra {_brl(ce)} acima do teto {_brl(limites.custo_extra_maximo)} (+{_brl(ce - limites.custo_extra_maximo)}).",
        ),
        _criterio_teto(
            "parcela",
            "Parcela moto nova",
            PESOS["parcela"],
            par,
            limites.parcela_maxima_nova,
            "R$",
            ok=f"Parcela {_brl(par)} dentro do teto {_brl(limites.parcela_maxima_nova)}.",
            atencao=f"Parcela {_brl(par)} próxima do teto ({par / limites.parcela_maxima_nova * 100:.0f}% do limite).",
            critico=f"Parcela {_brl(par)} acima do teto {_brl(limites.parcela_maxima_nova)} — compromete o orçamento.",
        ),
        _criterio_teto(
            "prazo_saldo",
            "Prazo saldo financiado",
            PESOS["prazo_saldo"],
            prazo,
            float(limites.prazo_max_receber_saldo_meses),
            "meses",
            ok="Saldo financiado entra no prazo aceitável.",
            atencao=f"Recebimento do saldo em {int(prazo)} mês(es) — monitore fluxo de caixa.",
            critico=f"Risco de caixa: saldo só em {int(prazo)} mês(es); limite é {int(limites.prazo_max_receber_saldo_meses)}.",
        ),
        _criterio_piso(
            "entrada_comprador",
            "Entrada do comprador",
            PESOS["entrada_comprador"],
            ent,
            limites.entrada_minima_comprador,
            ok=f"Entrada {_brl(ent)} atende o mínimo {_brl(limites.entrada_minima_comprador)}.",
            atencao=f"Entrada {_brl(ent)} pouco acima do mínimo — pouca folga na negociação.",
            critico=f"Entrada {_brl(ent)} abaixo do mínimo {_brl(limites.entrada_minima_comprador)} (faltam {_brl(limites.entrada_minima_comprador - ent)}).",
        ),
    ]

    if limites.cet_maximo_tolerado_pct is not None and taxa_efetiva is not None:
        criterios.append(
            _criterio_teto(
                "taxa_efetiva",
                "Taxa efetiva anual (compra)",
                PESOS["cet"],
                taxa_efetiva,
                limites.cet_maximo_tolerado_pct,
                "% a.a.",
                ok=f"Taxa efetiva {taxa_efetiva:.2f}% a.a. dentro do teto {limites.cet_maximo_tolerado_pct:.1f}%.",
                atencao=(
                    f"Taxa efetiva {taxa_efetiva:.2f}% a.a. próxima do teto "
                    f"({taxa_efetiva / limites.cet_maximo_tolerado_pct * 100:.0f}%)."
                ),
                critico=(
                    f"Taxa efetiva {taxa_efetiva:.2f}% a.a. acima do teto "
                    f"{limites.cet_maximo_tolerado_pct:.1f}%."
                ),
            )
        )

    if troca.desembolso_vista_agora > 0:
        gap = troca.desembolso_vista_agora
        criterios.append(
            CriterioDecisao(
                id="risco_caixa",
                nome="Risco de caixa imediato",
                peso=0,
                valor_atual=gap,
                limite=0.0,
                unidade="R$",
                pct_do_limite=100.0,
                severidade=Severidade.ATENCAO,
                mensagem=f"Você precisa de {_brl(gap)} à vista agora até entrar o saldo financiado — risco operacional.",
                pontos_risco=0.0,
            )
        )

    pontuacao = _pontuacao_normalizada(criterios)
    sem, ver, msg, acoes = _semaforo_final(criterios, pontuacao)

    falhas = [c.mensagem for c in criterios if c.severidade == Severidade.CRITICO]
    atencoes = [c.mensagem for c in criterios if c.severidade == Severidade.ATENCAO]

    return ResultadoDecisao(
        semaforo=sem,
        veredito=ver,
        mensagem=msg,
        criterios=criterios,
        pontuacao_risco=pontuacao,
        custo_extra=ce,
        pct_custo_extra_do_limite=pct_ce,
        motivos_falha=falhas,
        motivos_atencao=atencoes,
        resumo_acoes=acoes,
    )


def cor_semaforo(semaforo: Semaforo) -> str:
    return {"verde": "#22c55e", "amarelo": "#eab308", "vermelho": "#ef4444"}[semaforo.value]


def icone_severidade(sev: Severidade) -> str:
    return {"ok": "✅", "atencao": "⚠️", "critico": "❌"}[sev.value]
