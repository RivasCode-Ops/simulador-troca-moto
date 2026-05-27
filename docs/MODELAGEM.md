# Modelagem de ideia — Simulador Troca de Moto (v2)

> Formato base: [`PROMPT/Modelagem-Ideia/TEMPLATE-SAIDA.md`](../../PROMPT/Modelagem-Ideia/TEMPLATE-SAIDA.md)  
> **Enquadramento v2:** decisão financeira pessoal (não modelagem de negócio)  
> Gate: **ESTRUTURAR** → MVP em `Simulador-Troca-Moto/`  
> Revisão: ver [`ANALISE-REVISAO.md`](./ANALISE-REVISAO.md)

---

## A. O que você me enviou (espelho)

| Tipo de material | Resumo em 1 linha |
|------------------|-------------------|
| Texto solto (copy da ideia) | Troca de moto sem capital total, usando venda financiada + financiamento da nova |

**Tema central:** simular a operação financeira de vender a moto atual (parte financiada) e comprar outra, minimizando perda.  
**Nível de clareza do material:** médio-alto (números fixos; falta taxa, prazo e modelo jurídico da venda)

**Camadas detectadas no material (v2):**

| Camada | O que é | Status |
|--------|---------|--------|
| 1 — Problema pessoal | Trocar de moto sem ter o dinheiro todo | **[F]** núcleo |
| 2 — Lógica financeira | 25k / 20k+5k / 30k / 20k+10k; comparar cenários | **[F]** núcleo |
| 3 — Produto futuro | App para outros motociclistas | **[H]** extensão possível, não central |

---

## B. Extração — o que existe na bagunça

| Elemento | Conteúdo extraído | F/H/? |
|----------|-------------------|-------|
| Problema ou dor | Quer moto nova (R$ 30k) sem caixa para pagar à vista ou completar a diferença na troca | F |
| Quem sofre | Você (vendedor da usada + comprador da nova) | F |
| Solução imaginada | Vender usada com R$ 20k entrada + R$ 5k financiados; usar os R$ 20k na entrada da nova e financiar R$ 10k | F |
| Alternativas citáveis | Troca na concessionária; venda à vista + um financiamento; transferência de financiamento ao comprador (fórum) | F / H |
| Concorrência (ferramentas) | Simuladores de banco/concessionária; planilha Excel | F |
| Diferencial do simulador | Encadear **dois** lados e comparar com troca “ideal” (25k + 5k à vista) | F |
| Recursos necessários | Simulador + premissas CET/juros; opcional consulta financeira/jurídica | F |
| Riscos | Juros; gap de R$ 5k; inadimplência se você for credor; taxas de transferência/quitação | F |

**Lacunas críticas:**
1. Taxa, prazo e CET do financiamento do **comprador** (e se os R$ 5k caem na hora).
2. Taxa, prazo e CET do financiamento da moto **nova**.
3. Modelo legal: transferência para o comprador vs venda com saldo financiado vs troca na loja.
4. **Limites de aceitação** — quanto de custo extra, parcela e prazo você aceita (ver seção H).

**Contexto de mercado (referência externa):**  
Em discussões sobre troca com moto ainda financiada, pontos recorrentes são: transferir o financiamento para o comprador (com análise de crédito e taxas), pagar a diferença à vista na troca na concessionária, ou evitar estruturas onde o saldo financiado supera o valor de mercado do bem. Fonte: [Pequenas Notáveis — tópico sobre troca com financiamento](https://www.pequenasnotaveis.net/threads/46633-Moto-financiada-apos-um-tempo-%C3%A9-possivel-trocar-por-outra-mesmo-pagando-ainda?mode=hybrid).

---

## C. Modelo recomendado

| Campo | Preencher |
|-------|-----------|
| **Modelo escolhido** | **M3 adaptado — Decisão financeira individual** |
| **Por que este e não outro** | O material é decisão de troca com restrição de caixa, não abertura de empresa. Plano Sebrae completo misturava “negócio futuro” com “decisão presente”. M3 adaptado mantém premissas, fluxo e prazos sem forçar mercado/marketing agora. |
| **Modelo secundário (opcional)** | M4 Proposta de valor — **somente** se houver validação de produto (bloco I) |
| **Estágio da ideia** | validação operacional (simular → decidir → executar) |
| **Gate** | **ESTRUTURAR** |

**Nota de enquadramento (v2):** documento = **estrutura de decisão pessoal** com MVP de apoio; não é pitch de startup.

---

## D. Orientação — o que é este modelo e como você usa

**O que é:** um quadro para decidir se a troca faz sentido **agora**, com números, riscos e limites que você define antes de negociar.

**Como usar no dia a dia:**
1. Preencha premissas financeiras (seção E.8) com cotações reais.
2. Defina limites aceitáveis (seção H) — custo extra máximo, parcela máxima, prazo para receber os R$ 5k.
3. Rode o simulador (`app.py`) e compare cenários.
4. Se algum limite for ultrapassado → **não fechar** ou renegociar (entrada do comprador, prazo, venda à vista dos 25k).
5. Só depois de executar a troca pessoal, avalie bloco I (produto futuro).

**O que este modelo NÃO resolve:** aprovação de crédito, modelo jurídico definitivo, precificação de mercado da sua moto.

---

## E. Modelo preenchido — Decisão financeira individual

| Seção | Conteúdo | F/H/? |
|-------|----------|-------|
| 1. Objetivo da decisão | Trocar moto de R$ 30k minimizando custo extra vs troca ideal (25k usada + 5k à vista) | F |
| 2. Situação atual | Moto usada ~R$ 25k; sem caixa para fechar diferença à vista | F |
| 3. Plano em análise | Venda 20k + 5k financiados pelo comprador; compra 20k entrada + 10k financiados por você | F |
| 4. Referência (baseline) | Troca direta na loja: R$ 5k à vista, zero juros | F |
| 5. Alternativas a simular | (a) Comprador paga 25k à vista / financia 25k no banco dele (b) Entrada 22–25k (c) Transferência de financiamento ao comprador (d) Esperar e juntar caixa | F |
| 6. Ferramenta de apoio | Simulador local: Price, custo extra vs ideal, comparativo | F |
| 7. Plano operacional (90 dias) | Cotar taxas → simular 3 prazos → negociar comprador → validar loja → fechar venda → fechar compra | F |
| 8. Premissas financeiras | Usada 25k; nova 30k; entrada comprador 20k; saldo venda 5k; entrada loja 20k; saldo compra 10k; taxas mercado 1,5–3,5% a.m. | F |
| 9. Riscos da operação | Dois juros; gap dos 5k; CET alto; comprador não aprovar crédito; loja não aceitar entrada “por fora” | F |
| ~~Mercado / marketing / produto SaaS~~ | *Removido do núcleo — ver seção I* | — |

---

## F. Viabilidade preliminar (dupla nota)

### F.1 — Viabilidade da operação pessoal (troca agora)

| Critério | Avaliação | Comentário |
|----------|-----------|------------|
| Problema real | alto | Upgrade sem liquidez é comum |
| Clareza dos números-base | alto | 25 / 20 / 5 / 30 / 10 explícitos |
| Executabilidade sem produto | médio-alto | Planilha ou simulador bastam |
| Dependência de terceiros | alto (risco) | Comprador, financeira, concessionária |
| Complexidade jurídica | médio | Transferência vs venda com saldo |

**Nota — operação pessoal:** **7,5/10** (estruturação da ideia **8/10**; falta fechar limites H e taxas reais)

### F.2 — Viabilidade de virar produto (futuro)

| Critério | Avaliação | Comentário |
|----------|-----------|------------|
| Dor de mercado | médio | Existe, mas já há simuladores genéricos |
| Cliente pagante | baixo-médio | Não validado; hipótese |
| Diferenciação | médio | Dupla ponta é nicho |
| Complexidade regulatória | alto | Não é recomendação financeira |

**Nota — modelagem de negócio:** **6/10** — prematura; não bloqueia o MVP pessoal

---

## G. Próximos passos

| # | Ação | Prazo | Responsável |
|---|------|-------|-------------|
| 1 | Preencher seção H (limites aceitáveis) | 2 dias | você |
| 2 | Rodar simulador com CET/taxa reais (loja + financeira) | 7 dias | você |
| 3 | Simular cenário “venda 25k à vista + financiar só 5k na nova” | 7 dias | você |
| 4 | Confirmar com loja: entrada 20k com venda por fora | 14 dias | você |
| 5 | Negociar comprador até cenário ficar dentro dos limites H | 21 dias | você |

**Roteamento técnico:**
- [x] Modelagem v1
- [x] Modelagem v2 (decisão pessoal)
- [x] MVP simulador
- [ ] Critérios H no simulador (alertas verde/vermelho)
- [ ] `Projeto Novo/001-DESCOBERTA` **somente** se bloco I for validado

---

## H. Regras de decisão — limites aceitáveis da troca

*Preencher com seus números reais. O simulador deve comparar cenários contra estes limites.*

| Regra | Sua meta (preencher) | Exemplo ilustrativo | Se ultrapassar |
|-------|----------------------|---------------------|----------------|
| **Custo extra máximo** vs troca ideal (5k à vista) | R$ ______ | R$ 4.000 | Renegociar ou adiar |
| **Parcela máxima** da moto nova | R$ ______ / mês | R$ 400 | Aumentar entrada ou prazo menor com taxa menor |
| **Prazo máximo** do seu financiamento (nova) | ___ meses | 36 | Evitar 48x+ se CET subir muito |
| **Prazo máximo** para receber os R$ 5k do comprador | ___ meses / imediato | Imediato (financeira libera) | Não fechar sem crédito aprovado do comprador |
| **CET máximo** aceitável (moto nova) | ___ % a.a. | A cotar na loja | Buscar outra financeira ou adiar |
| **Entrada mínima** do comprador da usada | R$ ______ | R$ 22.000 | Recusar ou buscar outro comprador |

**Critério de corte (quando NÃO trocar):**
- Custo extra simulado > limite da tabela acima, **ou**
- Parcela nova > orçamento mensal, **ou**
- Loja não aceita operação sem quitar/transferir financiamento corretamente, **ou**
- Comprador não aprova crédito para os R$ 5k e você teria que “carregar” o risco.

**Critério de “pode fechar”:**
- Cenário dentro de todos os limites H **e** alternativa “venda à vista + 1 financiamento” não for muito melhor com esforço razoável de negociação.

---

## I. Possível evolução futura (fora do núcleo)

> Bloco **[H]** — não faz parte da decisão presente. Revisitar só após troca pessoal concluída ou validação com 5+ pessoas.

| Hipótese | Conteúdo |
|----------|----------|
| Produto | Calculadora web/app para motociclistas em upgrade sem caixa |
| Mercado | Motos financiadas no BR; grupos de troca/compra |
| Canal | WhatsApp, grupos Facebook, OLX |
| Modelo de receita | Gratuito + afiliado concessionária / premium — **não definido** |
| Próximo passo de produto | `Projeto Novo/001-DESCOBERTA` |

---

## Matemática resumida (cenário base)

| Etapa | Valor |
|-------|-------|
| Patrimônio na moto usada | R$ 25.000 |
| Entrada que você recebe (venda) | R$ 20.000 |
| Saldo vendido ao comprador (financiado) | R$ 5.000 |
| Moto nova | R$ 30.000 |
| Entrada na concessionária | R$ 20.000 |
| Saldo que você financia (moto nova) | R$ 10.000 |

**Referência “mínima perda” (sem juros):** troca direta = R$ 25.000 (usada) + R$ 5.000 (à vista) = R$ 30.000.

**Custo extra (definição v2):** tudo que você desembolsa (à vista + parcelas totais) **menos** os R$ 5.000 da referência ideal.

O simulador calcula cenários e deve, na próxima iteração, sinalizar violação dos limites da seção H.
