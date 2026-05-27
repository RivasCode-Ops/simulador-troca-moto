# Simulador de Troca de Moto — Dashboard de Decisão

Simule a troca da sua moto antes de assumir o prejuízo.  
Compare venda, financiamento e custo extra em um dashboard que mostra se vale trocar agora, negociar melhor ou esperar.

> **Resumo:** dashboard de decisão que modela venda da usada + compra da nova, calcula parcelas, juros e custo extra, aplica seus limites pessoais (seção H) e indica, com semáforo, se a troca vale a pena, precisa de ajuste ou é melhor esperar.

## O que o app faz

- Modela **venda da moto usada** (entrada + saldo financiado para o comprador).
- Modela **compra da moto nova** (entrada + financiamento na loja/banco).
- Calcula **parcelas, juros, CET e custo extra total** da operação.
- Compara o plano atual com cenários como: mais entrada, menor prazo, venda à vista + um financiamento só, esperar e juntar mais.
- Aplica as **regras da seção H** (limites pessoais) e exibe um **semáforo de decisão**: verde, amarelo ou vermelho.
- Explica **por que o plano foi aprovado ou reprovado** e permite exportar os cenários em CSV/JSON.

## Como usar

1. Ajuste valores, juros, prazos e taxas na **sidebar**.
2. Veja os **4 KPIs principais** no topo: custo extra, parcela da nova, total a receber da usada e status da decisão.
3. Abra o painel “Por que reprovou / pontos de atenção” se o semáforo não estiver verde.
4. Compare os cenários na tabela e exporte os dados para guardar a simulação.

## Como rodar

```bash
cd Simulador-Troca-Moto
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Documentação

- [`docs/MODELAGEM.md`](docs/MODELAGEM.md) — modelagem v2 (decisão pessoal + seção H)
- [`docs/CHECKLIST-MELHORIAS-UX.md`](docs/CHECKLIST-MELHORIAS-UX.md) — checklist de UX do dashboard
- [`docs/MI00-CONTEUDO-BRUTO.md`](docs/MI00-CONTEUDO-BRUTO.md) — ideia original

## Estrutura

```
app.py              # dashboard Streamlit
src/
  financiamento.py  # Tabela Price
  operacao.py       # venda + compra
  decisao.py        # semáforo e limites H
  cenarios.py       # cenários comparados
  exportacao.py     # CSV / JSON
docs/
```

MVP local — não substitui assessoria financeira ou jurídica.
