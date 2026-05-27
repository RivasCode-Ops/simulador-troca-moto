# Referências GitHub e mercado

Não existe repositório popular focado em **troca de moto com dupla financiamento (venda + compra) no Brasil**. O que existe são peças reutilizáveis:

## Mais próximos do problema

| Repositório | O que aproveitar | Gap para este projeto |
|-------------|------------------|------------------------|
| [ipagdevs/desafio-junior](https://github.com/ipagdevs/desafio-junior) | Exercício de simulador Price (veículo/imóvel), fórmulas PMT e CET | Um empréstimo só; sem troca |
| [soaringbeauty/tabelaprice](https://github.com/soaringbeauty/tabelaprice) | Tabela Price em Python, amortização por parcela | Acadêmico; sem UI nem cenários |
| [wsmhj/carpaymentcalculator](https://github.com/wsmhj/carpaymentcalculator) | Entrada + trade-in + comparador de prazos + modo reverso (“quanto posso pagar”) | EUA; impostos estaduais; não CDC entre particulares |
| [mindpowered/car-loan-calculator-js](https://github.com/mindpowered/car-loan-calculator-js) | API: preço, entrada, trade-in, taxa, prazo | JS; trade-in na concessionária, não venda financiada a terceiro |
| [ErezNagar/lease-calculator](https://github.com/ErezNagar/lease-calculator) | Financiamento + entrada + trade-in no total financiado | Leasing EUA |

## Stack sugerida (alinhada ao ecossistema encontrado)

- **Python + Streamlit** — padrão em simuladores BR ([nepeconunb/Cost-Accounting](https://github.com/nepeconunb/Cost-Accounting), [celloweb-ai/Assistente_Financeiro](https://github.com/celloweb-ai/Assistente_Financeiro))
- **Tabela Price** — padrão de bancos/financeiras para moto no Brasil
- **Opcional:** SAC como segundo sistema de amortização (menos comum em moto, mas útil para comparar)

## Diferencial deste projeto

1. Dois financiamentos encadeados (comprador da moto usada + sua moto nova).
2. Cenário de referência: troca direta 25k + 5k à vista vs plano híbrido.
3. Métrica **“custo extra vs ideal”** (juros + gap de entrada + taxas).
4. Premissas editáveis (taxa, prazo, taxas de contrato, quando os R$ 5 mil caem no bolso).

## Fontes de mercado (fora do GitHub)

- Simuladores de concessionária/banco (Itaú, Honda, etc.) — parcela única.
- Artigos BR: taxa típica **1,5% a 3,5% a.m.** em financiamento de moto; comparar **CET**, não só a parcela.
