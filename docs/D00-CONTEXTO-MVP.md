# D00 — Contexto da sessão (MVP app)

| Campo | Valor |
|-------|-------|
| **Projeto** | Simulador Troca de Moto |
| **Tipo** | MVP local — dashboard de decisão |
| **Stack** | Python 3 · Streamlit · Pandas |
| **Gate modelagem** | ESTRUTURAR (v2 decisão pessoal) |
| **Gate entrega** | MVP dashboard 4 blocos + semáforo H |

## O que construir

App **simples, direto e orientado à decisão** (não só calculadora de parcela):

1. Dados da operação (sidebar)
2. Resultado venda usada
3. Resultado compra nova
4. Comparação + semáforo (limites seção H)

## Saídas obrigatórias

- Parcela comprador · total recebido · parcela nova · total pago banco
- Juros embutidos vs juros pagos · custo extra vs troca ideal
- Verde / amarelo / vermelho

## Fora de escopo (agora)

- SaaS, login, banco de dados
- Assessoria jurídica automatizada

## Rodar

```bash
streamlit run app.py
```
