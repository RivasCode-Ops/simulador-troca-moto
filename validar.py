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
from src.financiamento import parcela_price  # noqa: E402
from src.operacao import DadosOperacao, simular_troca  # noqa: E402


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


def test_semaforo_vermelho() -> None:
    t = simular_troca(DadosOperacao(prazo_compra_meses=36, taxas_contrato_compra=500.0))
    dec = avaliar_decisao(t, LimitesDecisao())
    if dec.semaforo != Semaforo.VERMELHO:
        _fail(f"semáforo esperado vermelho, veio {dec.semaforo.value}")
    if dec.custo_extra <= LimitesDecisao().custo_extra_maximo:
        _fail("custo extra deveria ultrapassar limite padrão")
    _ok("Semáforo vermelho com limites padrão da seção H")


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
