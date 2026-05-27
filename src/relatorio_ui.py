"""Renderização Streamlit do relatório da simulação."""

from __future__ import annotations

import html
import json

import streamlit as st

from .decisao import cor_semaforo, Semaforo
from .relatorio import LinhaRelatorio, RelatorioSimulacao
from .ui import md_escape


def _css_relatorio() -> str:
    return """
    <style>
    .relatorio-sim {
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 0.5rem 0 1rem 0;
        background: rgba(15, 23, 42, 0.45);
    }
    .relatorio-sim h3 {
        font-size: 0.95rem;
        font-weight: 600;
        margin: 1.1rem 0 0.5rem 0;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0;
    }
    .relatorio-sim h3:first-of-type { margin-top: 0.35rem; }
    .relatorio-sim-header {
        margin-bottom: 0.75rem;
    }
    .relatorio-sim-header .titulo {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0 0 0.25rem 0;
    }
    .relatorio-sim-header .meta {
        font-size: 0.8rem;
        color: #94a3b8;
        margin: 0;
    }
    .relatorio-sim-resumo {
        font-size: 0.95rem;
        line-height: 1.5;
        color: #cbd5e1;
        margin: 0.75rem 0;
    }
    .relatorio-sim-veredito {
        padding: 0.65rem 0.85rem;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .relatorio-sim-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
        gap: 0.5rem 1rem;
        margin: 0.35rem 0 0.5rem 0;
    }
    .relatorio-sim-item .rotulo {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #94a3b8;
        margin: 0;
    }
    .relatorio-sim-item .valor {
        font-size: 0.9rem;
        font-weight: 600;
        color: #f1f5f9;
        margin: 0.1rem 0 0 0;
    }
    .relatorio-sim ul.acoes {
        margin: 0.35rem 0 0 1rem;
        padding: 0;
        color: #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.45;
    }
    @media (prefers-color-scheme: light) {
        .relatorio-sim {
            background: #f8fafc;
            border-color: #e2e8f0;
        }
        .relatorio-sim-header .titulo { color: #0f172a; }
        .relatorio-sim-resumo { color: #334155; }
        .relatorio-sim-item .valor { color: #0f172a; }
        .relatorio-sim h3 { color: #1e293b; border-color: #e2e8f0; }
    }
    </style>
    """


def _e(texto: str) -> str:
    return html.escape(str(texto))


def _html_grid(itens: tuple[LinhaRelatorio, ...]) -> str:
    cells = "".join(
        f'<div class="relatorio-sim-item"><p class="rotulo">{_e(r.rotulo)}</p>'
        f'<p class="valor">{_e(r.valor)}</p></div>'
        for r in itens
    )
    return f'<div class="relatorio-sim-grid">{cells}</div>'


def _html_secao(titulo: str, itens: tuple[LinhaRelatorio, ...]) -> str:
    return f"<h3>{_e(titulo)}</h3>{_html_grid(itens)}"


def render_relatorio_simulacao(relatorio: RelatorioSimulacao) -> None:
    st.markdown(_css_relatorio(), unsafe_allow_html=True)

    cor = cor_semaforo(Semaforo(relatorio.semaforo))
    veredito_html = (
        f'<div class="relatorio-sim-veredito" style="background:{cor}22;border-left:4px solid {cor};">'
        f"<strong>{_e(relatorio.decisao_titulo)}</strong> · {_e(relatorio.veredito)} · "
        f"Risco {relatorio.pontuacao_risco:.0f}/100</div>"
    )

    corpo = [
        '<div class="relatorio-sim">',
        '<div class="relatorio-sim-header">',
        f'<p class="titulo">{_e(relatorio.identificacao)}</p>',
        f'<p class="meta">Gerado em {_e(relatorio.gerado_em)}</p>',
        "</div>",
        veredito_html,
        f'<p class="relatorio-sim-resumo">{_e(relatorio.resumo_executivo)}</p>',
        _html_secao("KPIs principais", relatorio.kpis),
        _html_secao("Venda da usada", relatorio.venda),
        _html_secao("Compra da nova", relatorio.compra),
    ]

    if relatorio.fipe:
        corpo.append(_html_secao("Comparação FIPE", relatorio.fipe))
    else:
        corpo.append(
            "<h3>Comparação FIPE</h3>"
            '<p class="relatorio-sim-resumo">Consulta FIPE não realizada nesta sessão.</p>'
        )

    corpo.append(_html_secao("Custo extra da troca", relatorio.custo_extra))

    if relatorio.criterios:
        corpo.append("<h3>Análise do semáforo (seção H)</h3>")
        corpo.append(_html_grid(
            tuple(
                LinhaRelatorio(
                    f"{c.nome} ({c.status})",
                    f"{c.uso_limite} do limite · peso {c.peso_pct}",
                )
                for c in relatorio.criterios
            )
        ))
        for c in relatorio.criterios:
            if c.status != "OK":
                corpo.append(
                    f'<p class="relatorio-sim-resumo" style="font-size:0.85rem;">'
                    f"<strong>{_e(c.nome)}:</strong> {_e(c.mensagem)}</p>"
                )

    if relatorio.limites_h:
        corpo.append(_html_secao("Limites configurados", relatorio.limites_h))

    if relatorio.recomendacoes:
        corpo.append("<h3>Recomendações</h3><ul class=\"acoes\">")
        for r in relatorio.recomendacoes:
            corpo.append(f"<li>{_e(r)}</li>")
        corpo.append("</ul>")

    if relatorio.avisos:
        corpo.append("<h3>Avisos da operação</h3><ul class=\"acoes\">")
        for a in relatorio.avisos:
            corpo.append(f"<li>{_e(a)}</li>")
        corpo.append("</ul>")

    corpo.append("</div>")
    st.markdown("".join(corpo), unsafe_allow_html=True)

    with st.expander("Exportar relatório (preparado para PDF)", expanded=False):
        st.caption("Use JSON ou Markdown abaixo; exportação em PDF virá em versão futura.")
        c1, c2 = st.columns(2)
        c1.download_button(
            "Baixar relatório (JSON)",
            data=json.dumps(relatorio.para_dict(), ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="relatorio_simulacao.json",
            mime="application/json",
            key="dl_rel_json",
        )
        c2.download_button(
            "Baixar relatório (Markdown)",
            data=relatorio.para_markdown().encode("utf-8"),
            file_name="relatorio_simulacao.md",
            mime="text/markdown",
            key="dl_rel_md",
        )
        st.markdown(md_escape("Pré-visualização em texto:"))
        st.text(relatorio.para_markdown()[:4000])
