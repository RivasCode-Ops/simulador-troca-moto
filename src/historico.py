"""Histórico de simulações na sessão Streamlit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from .decisao import ResultadoDecisao
from .operacao import DadosOperacao, ResultadoTroca

MAX_SNAPSHOTS_SESSAO = 5
SESSION_KEY = "historico_simulacoes"

METRICAS_COMPARACAO: list[tuple[str, str]] = [
    ("custo_extra", "Custo extra"),
    ("parcela_nova", "Parcela moto nova"),
    ("total_receber_usada", "Total a receber (usada)"),
    ("total_desembolsado", "Total pago / desembolsado"),
    ("juros_totais", "Juros (seu bolso)"),
]


@dataclass(frozen=True)
class SnapshotSimulacao:
    rotulo: str
    salvo_em: str
    moto_usada: float
    moto_nova: float
    entrada_comprador: float
    entrada_loja: float
    taxa_compra_pct: float
    prazo_compra_meses: int
    taxa_venda_pct: float
    prazo_venda_meses: int
    custo_extra: float
    parcela_nova: float
    total_receber_usada: float
    total_desembolsado: float
    juros_totais: float
    semaforo: str
    pontuacao_risco: float

    def para_dict(self) -> dict:
        return asdict(self)


def criar_snapshot(
    rotulo: str,
    dados: DadosOperacao,
    troca: ResultadoTroca,
    decisao: ResultadoDecisao,
) -> dict:
    snap = SnapshotSimulacao(
        rotulo=rotulo.strip() or "Sem nome",
        salvo_em=datetime.now().strftime("%d/%m %H:%M"),
        moto_usada=dados.valor_moto_usada,
        moto_nova=dados.valor_moto_nova,
        entrada_comprador=dados.entrada_comprador,
        entrada_loja=dados.entrada_loja,
        taxa_compra_pct=dados.taxa_compra_mensal_pct,
        prazo_compra_meses=dados.prazo_compra_meses,
        taxa_venda_pct=dados.taxa_venda_mensal_pct,
        prazo_venda_meses=dados.prazo_venda_meses,
        custo_extra=troca.custo_extra_vs_ideal,
        parcela_nova=troca.compra.parcela_moto_nova,
        total_receber_usada=troca.venda.total_recebido_pelo_vendedor,
        total_desembolsado=troca.total_desembolsado_operacao,
        juros_totais=troca.juros_total_seu_bolso,
        semaforo=decisao.semaforo.value,
        pontuacao_risco=decisao.pontuacao_risco,
    )
    return snap.para_dict()


def adicionar_ao_historico(historico: list[dict], snapshot: dict) -> list[dict]:
    return [snapshot, *historico][:MAX_SNAPSHOTS_SESSAO]


def rotulo_completo(snap: dict) -> str:
    risco = snap.get("pontuacao_risco")
    extra = f" · risco {risco:.0f}" if risco is not None else ""
    return f"{snap['rotulo']} ({snap['salvo_em']}){extra}"


def rotulo_opcao(snap: dict, prefixo: str = "") -> str:
    return f"{prefixo}{snap['rotulo']} ({snap['salvo_em']})"


def listar_opcoes_comparacao(atual: dict, historico: list[dict]) -> list[tuple[str, dict]]:
    opcoes: list[tuple[str, dict]] = [("atual", atual)]
    for i, s in enumerate(historico):
        opcoes.append((s.get("id", f"h{i}"), s))
    return opcoes


def linhas_comparacao(atual: dict, historico: list[dict]) -> list[dict]:
    linhas = [
        {
            "Nome": "[Atual]",
            "Quando": "agora",
            "Custo extra": atual["custo_extra"],
            "Parcela nova": atual["parcela_nova"],
            "Total receber": atual["total_receber_usada"],
            "Semáforo": atual["semaforo"],
        }
    ]
    for s in historico:
        linhas.append(
            {
                "Nome": s["rotulo"],
                "Quando": s["salvo_em"],
                "Custo extra": s["custo_extra"],
                "Parcela nova": s["parcela_nova"],
                "Risco": s.get("pontuacao_risco", "—"),
                "Semáforo": s["semaforo"],
            }
        )
    return linhas


def comparar_duas(a: dict, b: dict, nome_a: str, nome_b: str) -> list[dict]:
    linhas: list[dict] = []
    for chave, titulo in METRICAS_COMPARACAO:
        va = float(a.get(chave, 0))
        vb = float(b.get(chave, 0))
        linhas.append(
            {
                "Métrica": titulo,
                nome_a: va,
                nome_b: vb,
                "Delta (B − A)": round(vb - va, 2),
            }
        )
    linhas.append(
        {
            "Métrica": "Semáforo",
            nome_a: a.get("semaforo", "—"),
            nome_b: b.get("semaforo", "—"),
            "Delta (B − A)": "—",
        }
    )
    return linhas


def dados_grafico_comparacao(a: dict, b: dict, nome_a: str, nome_b: str) -> dict[str, list]:
    """Séries numéricas para st.bar_chart (sem semáforo)."""
    metricas = [titulo for _, titulo in METRICAS_COMPARACAO]
    return {
        "Métrica": metricas,
        nome_a: [float(a.get(chave, 0)) for chave, _ in METRICAS_COMPARACAO],
        nome_b: [float(b.get(chave, 0)) for chave, _ in METRICAS_COMPARACAO],
    }


def delta_vs_ultimo_salvo(atual: dict, historico: list[dict]) -> dict[str, float] | None:
    if not historico:
        return None
    ultimo = historico[0]
    return {
        "custo_extra": round(atual["custo_extra"] - ultimo["custo_extra"], 2),
        "parcela_nova": round(atual["parcela_nova"] - ultimo["parcela_nova"], 2),
    }
