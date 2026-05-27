# Avaliação de QA — Simulador de Troca de Moto

**Data:** 2026-05-27  
**Escopo:** revisão cruzada entre relatório de QA externo e código em `src/` + `app.py`  
**Versão analisada:** pós-FIPE online + histórico persistente  

---

## Notas consolidadas

| Dimensão | Nota | Comentário |
|----------|-----:|------------|
| Clareza do relatório de QA | **9,5/10** | Cenários, severidade, evidência e ação — muito acima da média |
| Qualidade da triagem | **9/10** | Crítico / grave / moderado / leve alinhado a práticas de priorização |
| Confiabilidade das conclusões | **8/10** | Maioria confirmada no código; 3 itens reclassificados abaixo |
| Base conceitual do produto | **9/10** | Dupla ponta, Price, cenários, FIPE e semáforo H fazem sentido |
| Implementação atual | **6,5/10** | Valor real, mas falhas bloqueantes em cálculo, robustez e UI |
| **Prontidão geral do app** | **6,5/10** | Não pronto para produção; bom para rodada de estabilização |
| Potencial pós-correções P0–P1 | **8,5/10** | Núcleo financeiro sólido; correções são localizadas |

**Relatório de QA (como documento):** **8,8/10**

---

## Veredito executivo

O produto **já entrega decisão útil** (custo extra, semáforo, FIPE, histórico em disco), mas **não deve ser tratado como confiável em produção** até corrigir itens P0/P1 abaixo.

Decisão prática: **rodada focada de correção** (1–2 sprints curtos) antes de divulgar para terceiros ou usar como única base de negociação.

---

## O que está muito bom (confirmado)

| Área | Evidência no repo |
|------|------------------|
| Arquitetura por módulos | `financiamento`, `operacao`, `decisao`, `cenarios`, `fipe`, `persistencia` |
| Fluxo dupla ponta | `simular_troca()` encadeia venda + compra e custo extra vs ideal |
| Tabela Price | `parcela_price` / `tabela_price` com teste em `validar.py` |
| Semáforo com critérios nomeados | `decisao.py` — pesos, severidade, mensagens por critério |
| FIPE online | `fipe.py` + UI em cascata; cobertura do custo extra |
| Histórico persistente | `data/simulacoes.json` + reabrir parâmetros |
| Validação repetível | `validar.py` (sem UI) |

---

## Achados verificados no código

Legenda: **Confirmado** = reproduzido ou lido no fonte · **Parcial** = problema existe com nuance · **Não confirmado** = relatório exagerou ou desatualizado

### P0 — Crítico

| ID | Achado | Status | Resolução |
|----|--------|--------|-----------|
| P0-1 | Comparação A/B quebrava com `.style.format()` | **Resolvido** | `comparar_duas_para_exibicao()` — BRL só em linhas numéricas |
| P0-2 | Entrada loja > valor moto nova → financiamento fantasma | **Resolvido** | `financiamento_vazio()` + avisos em sidebar e `troca.avisos` |
| P0-3 | Entrada comprador > valor usada sem feedback | **Resolvido** | Saldo 0 + avisos; testes em `validar.py` |

### P1 — Grave (cálculo / decisão)

| ID | Achado | Status | Evidência |
|----|--------|--------|-----------|
| P1-1 | **CET exibido não é CET a.a.** | **Confirmado** | `financiamento.py` L69: `cet = (total_pago/pv - 1) * 100` — custo total relativo ao PV, **não** taxa anual efetiva \((1+i_m)^{12}-1\) nem CET regulatório |
| P1-2 | **Pontuação “/100” com teto efetivo 90** quando CET não entra nos critérios | **Confirmado** | `PESOS` soma 100, mas `avaliar_decisao` só adiciona critério CET se `cet_maximo_tolerado_pct` definido (padrão: desligado). Máximo = 35+30+20+5 = **90**; UI mostra `risco X/100` |
| P1-3 | Semáforo vs score podem parecer desalinhados ao usuário | **Parcial** | Lógica em `_semaforo_final`: vermelho por qualquer crítico; amarelo se `pontuacao >= 25` **ou** atenções. Cenário base: 50/100 + vermelho — **correto pelo código**, mas **confuso na UI** sem legenda |

### P2 — Moderado (robustez / domínio)

| ID | Achado | Status | Evidência |
|----|--------|--------|-----------|
| P2-1 | Falta validação preventiva na sidebar (entradas > valores, taxa 0, etc.) | **Confirmado** | `app.py` só usa `number_input` sem checagem pré-cálculo |
| P2-2 | `risco_caixa` com peso 0 na tabela mas aparece como critério | **Confirmado** | `decisao.py` L305–319 — informativo, não entra no score |
| P2-3 | Dependência de API FIPE sem fallback offline | **Confirmado** | `fipe.py` — erro amigável, mas simulação FIPE indisponível sem rede |

### P3 — Leve (UX / copy)

| ID | Achado | Status | Evidência |
|----|--------|--------|-----------|
| P3-1 | Locale misto (vírgula/ponto) em alguns textos | **Parcial** | `ui.brl` padroniza; `st.dataframe` style usa `decimal=","` — inconsistente em exports |
| P3-2 | Cards / métricas cortadas em telas estreitas | **Não verificado** | Requer teste visual Streamlit |
| P3-3 | Mensagens longas no semáforo | **Parcial** | Concatenação em `_semaforo_final` — legível, mas densa |

---

## Itens do relatório reclassificados

| Relatório original | Ajuste após leitura do código |
|--------------------|-------------------------------|
| Bug 3 — CET (fórmula composta) | **Confirmado** — crítica procede; não é só hipótese |
| Bug 11 — pesos somam 90% | **Parcial** — dict soma **100**; teto **efetivo 90** quando CET desligado (bug de escala, não de soma do dict) |
| Crash entrada loja > nova | **Reclassificado** — não crasha; **erro silencioso grave** (P0-2) |
| Crash ao salvar histórico | **Não reproduzido** no fluxo atual JSON; possível bug antigo `session_state`+styling — ver P0-1 na comparação |

---

## Prioridade de correção (backlog)

```
1. P0-1  Comparar A/B sem .style.format em linhas texto (ou subset numérico)
2. P0-2  Bloquear/aviso: entrada_loja >= valor_nova → sem financiamento fictício
3. P0-3  Aviso: entrada_comprador > valor_usada
4. P1-1  Renomear métrica ou implementar CET a.a. (composto) + tooltip
5. P1-2  Normalizar score: sempre /100 (escalar 90→100 ou incluir CET opcional com peso 10 inativo)
6. P1-3  Legenda: “50/90 critérios ativos” ou forçar critério CET informativo
7. P2-*  Validações sidebar + testes de regressão em validar.py
8. P3-*  Polimento UX após estabilização
```

---

## Cobertura de testes atual

| Área | `validar.py` | Lacuna |
|------|:------------:|--------|
| Price / cenário base | ✅ | — |
| FIPE parse / análise | ✅ | Sem teste de API (ok) |
| Persistência JSON | ✅ | — |
| Domínio entradas inválidas | ❌ | Adicionar após P0-2/P0-3 |
| CET / semáforo escala | ❌ | Adicionar após P1-1/P1-2 |
| Comparar_duas + styler | ❌ | Adicionar após P0-1 |

---

## Alinhamento com notas do revisor

| Afirmação do revisor | Concordância |
|----------------------|:--------------:|
| Relatório QA 8,8/10 | ✅ |
| App prontidão 6,5/10 | ✅ |
| Base conceitual 9/10 | ✅ |
| Potencial 8,5/10 pós-correções | ✅ |
| Não está pronto para produção | ✅ |
| Priorizar crashes → cálculo → semáforo → domínio → UX | ✅ (com P0-2 como “silencioso”, não crash) |

---

## Referências

- [FIPE API Parallelum](https://deividfortuna.github.io/fipe/)
- [Tabela FIPE — índice veículos](https://www.fipe.org.br/pt-br/indices/veiculos)
- CET anual efetiva (composição): \((1+i_{mensal})^{12}-1\)
- Streamlit + Styler: formatação numérica em colunas com strings misturadas — ver issue streamlit/pandas #3634

---

*Atualizar este documento após cada rodada de correção (marcar IDs como resolvidos com commit/PR).*
