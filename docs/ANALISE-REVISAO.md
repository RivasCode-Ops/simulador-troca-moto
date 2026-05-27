# Análise de revisão — Modelagem v1 → v2

Documento de resposta ao feedback recebido (anexo) + referência ao fórum [Pequenas Notáveis](https://www.pequenasnotaveis.net/threads/46633-Moto-financiada-apos-um-tempo-%C3%A9-possivel-trocar-por-outra-mesmo-pagando-ainda?mode=hybrid).

---

## 1. Pontuação (concordância com o anexo)

| Dimensão | Nota sugerida (anexo) | Nossa leitura | Comentário |
|----------|----------------------|---------------|------------|
| Estruturação da ideia | **8/10** | **8/10** | Material bruto bem organizado; lacunas certas |
| Modelagem de negócio | **6/10** | **6/10** | Partes de mercado/marketing eram extensão prematura |
| Operação pessoal (v2) | — | **7,5/10** | Sobe com enquadramento correto + seção H (a preencher) |

**Veredito:** a base estava boa; o problema era **enquadramento**, não falta de conteúdo.

---

## 2. Diagnóstico — três camadas misturadas (v1)

Na v1, três assuntos apareciam no mesmo fio:

```
┌─────────────────────────────────────────────────────────┐
│  Camada 1 — Problema pessoal (trocar moto sem caixa)   │  ← núcleo [F]
├─────────────────────────────────────────────────────────┤
│  Camada 2 — Lógica financeira (25/20/5/30/10)          │  ← núcleo [F]
├─────────────────────────────────────────────────────────┤
│  Camada 3 — Produto futuro (app, marketing, mercado)   │  ← [H] prematuro
└─────────────────────────────────────────────────────────┘
```

Isso levou a escolher **“Plano Sebrae”** como modelo principal, o que inflou seções E.4, E.6, E.9 e F (“cliente pagante”) sem virem do material original.

---

## 3. Pontos fortes mantidos (sem mudança de fundo)

- Problema bem definido: minimizar perda na troca sem capital total.
- Números-base claros e estáveis.
- Lacunas críticas corretas: taxa, prazo, CET, modelo legal.
- Plano operacional em G continua acionável.

---

## 4. Mudanças aplicadas (v1 → v2)

| # | O que o anexo pediu | O que mudou no documento |
|---|---------------------|---------------------------|
| 1 | Reclassificar foco: decisão financeira pessoal | **C:** “M3 adaptado — Decisão financeira individual” (substitui Plano Sebrae como rótulo principal) |
| 2 | Reduzir mercado/marketing no núcleo | **E:** removidas linhas de mercado, marketing e SWOT “produto digital”; movidas para **I** |
| 3 | Separar viabilidade pessoal vs produto | **F** dividido em **F.1** (operação) e **F.2** (produto futuro) com notas distintas |
| 4 | Reescrever D para decisão presente | **D** foca fluxo: premissas → limites H → simulador → corte |
| 5 | Nova seção de critérios objetivos | **H — Regras de decisão** (custos, parcela, prazos, critério de não trocar) |
| 6 | Produto futuro em bloco separado | **I — Possível evolução futura** marcado como [H] |
| 7 | Manter A, B, G quase iguais | **A/B/G** preservados; **A** ganhou tabela das 3 camadas |
| 8 | Contexto de mercado sem confundir com negócio | **B** + link fórum: transferência de financiamento, riscos de assumir parcela |

---

## 5. O que foi removido ou rebaixado

| Item v1 | Status v2 |
|---------|-----------|
| “M3 — Plano Sebrae simplificado” como título do quadro E | Substituído por “Decisão financeira individual” |
| E.4 Mercado e clientes | → Seção **I** [H] |
| E.6 Estratégia de marketing | → Seção **I** [H] |
| E.3 Produto ou serviço (SaaS) no núcleo | → E.6 “Ferramenta de apoio” [F] + **I** [H] |
| F “Cliente pagante” como critério central | → só em **F.2** |
| Nota única “maturidade negócio 6/10” | → duas notas: operação **7,5/10**, negócio **6/10** |

---

## 6. O que foi acrescentado

### Seção H — Regras de decisão

Responde ao que faltava na v1: **como decidir**, não só calcular.

| Pergunta | Onde está |
|----------|-----------|
| Custo extra máximo aceitável? | H — tabela (a preencher) |
| Em quantos meses receber os R$ 5k? | H — prazo máximo |
| Parcela máxima da nova? | H — tabela |
| Quando não trocar? | H — critério de corte |

### Insight do fórum (não muda seus números, mas informa risco)

Do tópico em Pequenas Notáveis, pontos alinhados ao seu caso:

- **Transferência de financiamento** ao comprador exige aprovação de crédito e taxas (citado ~R$ 600 em caso real no fórum).
- Troca na concessionária costuma exigir **quitar diferença à vista** ou estrutura formal.
- Risco clássico: saldo financiado **maior que valor de mercado** do bem — evitar estrutura onde você “carrega” o risco dos R$ 5k sem garantia.

Isso reforça sua lacuna 3 (modelo legal) e a regra H de só fechar com crédito do comprador aprovado.

---

## 7. Resumo executivo da revisão

| Afirmação (anexo) | Situação após v2 |
|-------------------|------------------|
| Bem modelado para MVP | Sim — gate ESTRUTURAR mantido |
| Não limpo como negócio na v1 | Corrigido — núcleo = decisão pessoal |
| Centro = decisão da troca | Sim — C, D, E, F.1, H |
| Faltavam limites de aceitação | Sim — seção H (campos em branco para você preencher) |
| Produto futuro separado | Sim — seção I |

---

## 8. Pendências (próxima iteração técnica)

1. **Você preencher** os campos em branco da seção H.
2. **Simulador:** alertas quando cenário ultrapassar limites H (hoje só calcula).
3. **Não abrir** `001-DESCOBERTA` até bloco I ter validação mínima.

---

## 9. Arquivos

| Arquivo | Versão |
|---------|--------|
| `MODELAGEM.md` | **v2** (atual) |
| `ANALISE-REVISAO.md` | este documento |
| `MI00-CONTEUDO-BRUTO.md` | inalterado (fonte) |

Para ver a v1 original, consulte o histórico do Git do repositório (commit anterior à revisão), se versionado.
