# 10 — Etapa 3: correções financeiras

## Objetivo

Tornar as recorrências mais previsíveis e alinhar a apresentação dos valores à moeda selecionada.

## Alterações

- Corrigida a geração de recorrências mensais e anuais para preservar a data de referência.
- Evitado que a ocorrência em fevereiro altere o dia-base das próximas datas.
- Adicionado limite de processamento por recorrência para evitar execução excessiva.
- A função de formatação passou a considerar BRL, USD e EUR.
- Transferências, parcelamentos e pagamentos parciais foram revisados e testados.
- A regra de fechamento de fatura não foi alterada sem exemplos reais do emissor.

## Validação

19 testes automatizados aprovados e compilação dos arquivos principais.

## Limitações

A moeda selecionada altera a apresentação, mas não converte valores. O fechamento de fatura precisa de validação com as regras reais de cada cartão.
