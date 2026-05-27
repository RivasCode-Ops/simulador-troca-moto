"""
Validação repetível do simulador (sem UI).
Rodar: python validar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.cenarios import listar_cenarios, premissas_from_inputs  # noqa: E402
from src.decisao import LimitesDecisao, Semaforo, avaliar_decisao  # noqa: E402
from src.financiamento import parcela_price, taxa_efetiva_anual_pct  # noqa: E402
from src.decisao import peso_total_ativo  # noqa: E402
from src.fipe import FipePreco, parse_valor_fipe  # noqa: E402
from src.fipe_analise import analisar_fipe_vs_venda  # noqa: E402
from src import persistencia as persistencia  # noqa: E402
from src.historico import comparar_duas, comparar_duas_para_exibicao  # noqa: E402
from src.operacao import DadosOperacao, simular_troca  # noqa: E402
from src.decisao import explicar_custo_extra  # noqa: E402
from src.relatorio import montar_relatorio  # noqa: E402
from src.ui import (  # noqa: E402
    brl,
    mensagem_banner_resumo,
    pct,
    progresso_normalizado,
    tabela_amortizacao,
)
from src.validacao import tem_erro_bloqueante, validar_entradas  # noqa: E402


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f"  FALHA  {msg}")
    raise AssertionError(msg)


def test_price() -> None:
    pmt = parcela_price(10_000, 0.02, 12)
    if not (900 < pmt < 950):
        _fail(f"parcela Price inesperada: {pmt}")
    _ok("Tabela Price (parcela em faixa esperada)")


def test_cenario_base() -> None:
    d = DadosOperacao(
        prazo_venda_meses=24,
        prazo_compra_meses=36,
        taxas_contrato_compra=500.0,
    )
    t = simular_troca(d)
    if abs(t.ideal.diferenca_a_vista - 5_000) > 0.01:
        _fail(f"gap ideal deveria ser 5000, veio {t.ideal.diferenca_a_vista}")
    if abs(t.custo_extra_vs_ideal - 9_829.84) > 0.5:
        _fail(f"custo extra esperado ~9829.84, veio {t.custo_extra_vs_ideal}")
    if abs(t.compra.parcela_moto_nova - 411.94) > 0.1:
        _fail(f"parcela nova esperada ~411.94, veio {t.compra.parcela_moto_nova}")
    _ok("Cenário base (custo extra, parcela, gap ideal)")


def test_taxa_efetiva_anual() -> None:
    t2 = taxa_efetiva_anual_pct(0.02)
    if abs(t2 - 26.82) > 0.05:
        _fail(f"2% a.m. → efetiva ~26,82%, veio {t2}")
    t01 = taxa_efetiva_anual_pct(0.001)
    if abs(t01 - 1.21) > 0.05:
        _fail(f"0,1% a.m. → efetiva ~1,21%, veio {t01}")
    _ok("Taxa efetiva anual composta (2% e 0,1% a.m.)")


def test_score_normalizado() -> None:
    t = simular_troca(DadosOperacao(prazo_compra_meses=36, taxas_contrato_compra=500.0))
    dec = avaliar_decisao(t, LimitesDecisao())
    if dec.pontuacao_risco < 0 or dec.pontuacao_risco > 100:
        _fail(f"score fora de 0–100: {dec.pontuacao_risco}")
    if dec.semaforo != Semaforo.VERMELHO:
        _fail("cenário base deveria ser vermelho")
    if not (54 <= dec.pontuacao_risco <= 58):
        _fail(f"score normalizado esperado ~56, veio {dec.pontuacao_risco}")
    if peso_total_ativo(dec.criterios) != 90:
        _fail("sem limite CET, pesos ativos deveriam somar 90")

    lim_cet = LimitesDecisao(cet_maximo_tolerado_pct=40.0)
    dec_cet = avaliar_decisao(t, lim_cet)
    if peso_total_ativo(dec_cet.criterios) != 100:
        _fail("com limite CET, pesos ativos deveriam somar 100")
    if dec_cet.pontuacao_risco < 0 or dec_cet.pontuacao_risco > 100:
        _fail("score com CET fora de 0–100")
    if dec_cet.semaforo != dec.semaforo:
        _fail("semáforo deveria ser igual com/sem critério CET (mesmos fatos)")
    _ok("Score 0–100 com renormalização de pesos")


def test_semaforo_vermelho() -> None:
    t = simular_troca(DadosOperacao(prazo_compra_meses=36, taxas_contrato_compra=500.0))
    dec = avaliar_decisao(t, LimitesDecisao())
    if dec.semaforo != Semaforo.VERMELHO:
        _fail(f"semáforo esperado vermelho, veio {dec.semaforo.value}")
    if dec.custo_extra <= LimitesDecisao().custo_extra_maximo:
        _fail("custo extra deveria ultrapassar limite padrão")
    if dec.veredito.value != "Melhor esperar ou mudar o plano":
        _fail("veredito inconsistente com semáforo vermelho")
    _ok("Semáforo vermelho com limites padrão da seção H")


def test_parse_fipe() -> None:
    if parse_valor_fipe("R$ 25.000,00") != 25_000.0:
        _fail("parse_valor_fipe falhou")
    _ok("Parse de valor FIPE (R$ brasileiro)")


def test_analise_fipe() -> None:
    fipe = FipePreco(
        valor=20_000.0,
        codigo_fipe="123456-7",
        marca="Honda",
        modelo="CG",
        ano_modelo=2020,
        combustivel="Gasolina",
        mes_referencia="maio de 2026",
        tipo_veiculo=2,
        valor_texto="R$ 20.000,00",
    )
    a = analisar_fipe_vs_venda(fipe, preco_venda=25_000.0, custo_extra_troca=9_829.84)
    if a.diferenca_reais != 5_000.0:
        _fail(f"diferença esperada 5000, veio {a.diferenca_reais}")
    if a.cobertura_custo_extra_pct is None or a.cobertura_custo_extra_pct < 50:
        _fail(f"cobertura esperada ~51%, veio {a.cobertura_custo_extra_pct}")
    _ok("Análise FIPE vs venda e cobertura do custo extra")


def test_persistencia() -> None:
    import tempfile
    from pathlib import Path

    orig = persistencia.ARQUIVO
    with tempfile.TemporaryDirectory() as td:
        persistencia.ARQUIVO = Path(td) / "simulacoes.json"
        try:
            snap = {
                "id": "test-1",
                "rotulo": "Teste",
                "salvo_em": "01/01 00:00",
                "salvo_em_iso": "2026-01-01T00:00:00",
                "moto_usada": 25_000.0,
                "preco_alvo_usada": 25_000.0,
                "custo_extra": 9_000.0,
                "semaforo": "vermelho",
                "pontuacao_risco": 56.0,
                "veredito": "Melhor esperar ou mudar o plano",
                "fipe": {"preco_fipe": 20_000.0, "preco_venda": 25_000.0},
            }
            persistencia.salvar(snap)
            lista = persistencia.carregar()
            if len(lista) != 1 or lista[0]["rotulo"] != "Teste":
                _fail("persistencia.salvar/carregar falhou")
            if lista[0].get("veredito") != "Melhor esperar ou mudar o plano":
                _fail("veredito não persistido")
            if not persistencia.excluir("test-1"):
                _fail("excluir deveria retornar True")
            if persistencia.carregar():
                _fail("lista deveria estar vazia após excluir")
        finally:
            persistencia.ARQUIVO = orig
    _ok("Persistência JSON (salvar, carregar, excluir)")


def test_validacao_dominio_ui() -> None:
    erros = validar_entradas(0, 30_000, 20_000, 20_000, 2.0, 2.0, 24, 36)
    if not tem_erro_bloqueante(erros):
        _fail("valor usada 0 deveria bloquear")
    if brl(1234.5) != "R$ 1.234,50":
        _fail(f"brl pt-BR esperado R$ 1.234,50, veio {brl(1234.5)}")
    if pct(26.82) != "26,82%":
        _fail(f"pct pt-BR esperado 26,82%, veio {pct(26.82)}")
    tab = tabela_amortizacao(
        [{"parcela": 1, "pagamento": 100.0, "juros": 10.0, "amortizacao": 90.0, "saldo": 900.0}]
    )
    if "Amortização" not in tab.columns or "R$" not in str(tab.iloc[0]["Pagamento"]):
        _fail("tabela amortização deveria ter colunas pt-BR e moeda formatada")
    _ok("Validação de domínio + formatação pt-BR")


def test_dominio_entradas() -> None:
    # P0-2: entrada loja > nova
    t1 = simular_troca(DadosOperacao(valor_moto_nova=20_000, entrada_loja=25_000))
    if t1.compra.valor_financiado_principal != 0 or t1.compra.financiamento.valor_financiado > 0.01:
        _fail(f"financiamento compra deveria ser zero, pv={t1.compra.financiamento.valor_financiado}")
    if t1.compra.parcela_moto_nova != 0:
        _fail("parcela compra deveria ser 0")
    if not any("loja" in a.lower() for a in t1.avisos):
        _fail("faltou aviso entrada loja")

    # entrada loja == nova
    t1b = simular_troca(DadosOperacao(valor_moto_nova=20_000, entrada_loja=20_000))
    if t1b.compra.parcela_moto_nova != 0:
        _fail("parcela compra deveria ser 0 quando entrada == valor nova")

    # P0-3: entrada comprador > usada
    t2 = simular_troca(DadosOperacao(valor_moto_usada=20_000, entrada_comprador=25_000))
    if t2.venda.saldo_financiado != 0:
        _fail("saldo venda deveria ser 0")
    if t2.venda.financiamento is not None:
        _fail("não deveria haver financiamento do comprador")
    if not any("comprador" in a.lower() for a in t2.avisos):
        _fail("faltou aviso entrada comprador")

    # entrada comprador == usada
    t2b = simular_troca(DadosOperacao(valor_moto_usada=20_000, entrada_comprador=20_000))
    if t2b.venda.saldo_financiado != 0 or t2b.venda.parcela_comprador != 0:
        _fail("venda sem saldo quando entrada == valor usada")

    _ok("Domínio: entradas >= valor moto (loja e comprador)")


def test_comparacao_ab_exibicao() -> None:
    a = {
        "custo_extra": 9000.0,
        "parcela_nova": 400.0,
        "total_receber_usada": 25000.0,
        "total_desembolsado": 35000.0,
        "juros_totais": 4000.0,
        "semaforo": "vermelho",
    }
    b = {**a, "custo_extra": 8000.0, "semaforo": "amarelo"}
    comparar_duas(a, b, "A", "B")
    df = comparar_duas_para_exibicao(a, b, "A", "B")
    sem_row = df[df["Métrica"] == "Semáforo"]
    if sem_row.empty or "vermelho" not in str(sem_row.iloc[0]["A"]):
        _fail("linha semáforo deveria preservar texto")
    if not str(df.iloc[0]["A"]).startswith("R$"):
        _fail("linha numérica deveria estar em BRL")
    _ok("Comparação A/B formatada (sem Styler em strings)")


def test_relatorio_simulacao() -> None:
    d = DadosOperacao(prazo_compra_meses=36, taxas_contrato_compra=500.0)
    t = simular_troca(d)
    dec = avaliar_decisao(t, LimitesDecisao())
    exp = explicar_custo_extra(t)
    rel = montar_relatorio(
        dados=d,
        troca=t,
        decisao=dec,
        limites=LimitesDecisao(),
        explicacao=exp,
        fipe=None,
    )
    if len(rel.kpis) < 4:
        _fail("relatório deve ter pelo menos 4 KPIs")
    if not rel.resumo_executivo or "Custo extra" not in rel.resumo_executivo:
        _fail("resumo executivo incompleto")
    if not rel.recomendacoes:
        _fail("relatório deve trazer recomendações")
    md = rel.para_markdown()
    if "Relatório da simulação" not in md or "KPIs principais" not in md:
        _fail("markdown do relatório incompleto")
    payload = rel.para_dict()
    if payload.get("semaforo") != dec.semaforo.value:
        _fail("dict do relatório com semáforo inconsistente")
    _ok("Relatório executivo montado (dict, markdown e seções)")


def test_banner_semaforo() -> None:
    loja = avaliar_decisao(simular_troca(DadosOperacao(entrada_loja=35_000)), LimitesDecisao())
    base = avaliar_decisao(simular_troca(DadosOperacao()), LimitesDecisao())

    msg_verde = mensagem_banner_resumo(loja)
    if "Reprovado" in msg_verde or "inviável" in msg_verde:
        _fail(f"banner verde não deve citar reprovação: {msg_verde}")
    if loja.semaforo != Semaforo.VERDE:
        _fail("entrada loja alta deveria ser semáforo verde")

    msg_vermelho = mensagem_banner_resumo(base)
    if base.semaforo != Semaforo.VERMELHO:
        _fail("cenário base deveria ser vermelho")
    if msg_vermelho.startswith("Reprovado:"):
        _fail("banner não deve repetir prefixo Reprovado:")
    if "inviável" not in msg_vermelho and "limite" not in msg_vermelho:
        _fail(f"mensagem vermelha esperada sobre limites: {msg_vermelho}")
    _ok("Banner alinhado ao semáforo (sem texto estático de reprovação no verde)")


def test_progresso_pct_ce() -> None:
    if progresso_normalizado(-40) != 0.0:
        _fail("progresso negativo deveria ser 0")
    if progresso_normalizado(120) != 1.0:
        _fail("progresso acima de 100% deveria ser 1")
    if abs(progresso_normalizado(56) - 0.56) > 1e-9:
        _fail("progresso 56% deveria ser 0.56")

    d_loja = DadosOperacao(valor_moto_nova=30_000.0, entrada_loja=35_000.0)
    dec_loja = avaliar_decisao(simular_troca(d_loja), LimitesDecisao())
    if dec_loja.pct_custo_extra_do_limite is not None and dec_loja.pct_custo_extra_do_limite < 0:
        _fail("pct custo extra vs limite não pode ser negativo")

    d_comp = DadosOperacao(valor_moto_usada=25_000.0, entrada_comprador=30_000.0)
    dec_comp = avaliar_decisao(simular_troca(d_comp), LimitesDecisao())
    if dec_comp.pct_custo_extra_do_limite is not None and dec_comp.pct_custo_extra_do_limite < 0:
        _fail("pct custo extra com entrada comprador alta não pode ser negativo")
    _ok("Clamp de st.progress e pct_custo_extra_do_limite >= 0")


def test_cenarios_lista() -> None:
    p = premissas_from_inputs(
        valor_usada=25_000,
        valor_nova=30_000,
        entrada_comprador=20_000,
        entrada_loja=20_000,
        taxa_venda=2.0,
        taxa_compra=2.0,
        prazo_venda=24,
        prazo_compra=36,
        taxas_venda=0,
        taxas_compra=500,
        libera_saldo=True,
    )
    cenarios = listar_cenarios(p)
    if len(cenarios) < 5:
        _fail(f"esperava pelo menos 5 cenários, veio {len(cenarios)}")
    nomes = {c.id for c in cenarios}
    for cid in ("ideal", "plano_atual", "mais_entrada", "menor_prazo"):
        if cid not in nomes:
            _fail(f"cenário '{cid}' ausente")
    _ok(f"{len(cenarios)} cenários nomeados presentes")


def main() -> int:
    testes = [
        ("Price", test_price),
        ("FIPE parse", test_parse_fipe),
        ("FIPE análise", test_analise_fipe),
        ("Persistência", test_persistencia),
        ("Validação UI", test_validacao_dominio_ui),
        ("Domínio entradas", test_dominio_entradas),
        ("Comparação A/B", test_comparacao_ab_exibicao),
        ("Taxa efetiva a.a.", test_taxa_efetiva_anual),
        ("Score /100", test_score_normalizado),
        ("Relatório simulação", test_relatorio_simulacao),
        ("Banner semáforo", test_banner_semaforo),
        ("Progresso / pct CE", test_progresso_pct_ce),
        ("Cenário base", test_cenario_base),
        ("Semáforo", test_semaforo_vermelho),
        ("Cenários", test_cenarios_lista),
    ]
    print("Validando Simulador de Troca de Moto\n")
    erros = 0
    for nome, fn in testes:
        print(f"[{nome}]")
        try:
            fn()
        except AssertionError:
            erros += 1
        print()
    if erros:
        print(f"Resultado: {erros} falha(s).")
        return 1
    print("Resultado: tudo OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
