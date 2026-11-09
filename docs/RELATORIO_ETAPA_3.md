# Finaxis — Relatório da Etapa 3: Correções financeiras

## Alterações implementadas

### 1. Lançamentos recorrentes
- Limitado o processamento a 500 ocorrências por recorrência em cada execução (configurável internamente, com teto de 5.000), evitando loops excessivos quando há datas muito antigas.
- Quando o limite é atingido, a próxima data permanece vencida e o processamento continua na execução seguinte.
- Corrigida a deriva de calendário em recorrências mensais: uma recorrência iniciada no dia 31 volta ao dia 31 nos meses seguintes quando esse dia existe, em vez de permanecer no dia 28 após fevereiro.
- O calendário anual também preserva o mês e o dia de referência, ajustando anos não bissextos para o último dia válido de fevereiro.

### 2. Valores monetários e moeda
- Mantido o uso de `Decimal` e arredondamento financeiro para duas casas.
- A formatação agora oferece símbolos BRL (R$), USD (US$) e EUR (€).
- A função de exibição da interface utiliza a moeda selecionada no perfil do usuário.

### 3. Transferências e cartões
- Revisados os fluxos existentes de transferência: as duas pontas são gravadas na mesma transação SQLite e os testes confirmam o saldo das contas.
- Revisados parcelamento, distribuição de centavos e pagamento parcial de fatura; os testes existentes confirmam a distribuição de R$ 100,00 em três parcelas (R$ 33,34 na primeira) e o estorno vinculado ao excluir o lançamento de pagamento.
- Não alterei a regra de competência/faturamento do cartão nesta etapa: ela depende da regra efetiva de fechamento e vencimento de cada emissor. A lógica atual está coberta por teste, mas precisa ser homologada com exemplos reais do cartão antes de ser considerada definitiva.

## Testes e validação
- `python -m unittest discover -s tests -v`: **19 testes aprovados**.
- `python -m py_compile app.py database.py`: aprovado.
- Foram acrescentados testes para recorrência mensal ancorada, limite de ocorrências e formatação BRL/USD/EUR.
- Os testes usam banco temporário; os bancos financeiros do projeto não foram usados como alvo de escrita.
- Não foi feita validação visual no navegador/Streamlit nem homologação com extratos reais de cartão.

## Pontos para a próxima homologação
- Confirmar com uma fatura real as regras de compra no dia do fechamento, compra após o fechamento, vencimento e parcelamento.
- Confirmar se a moeda do perfil deve alterar somente a apresentação ou também a moeda-base dos valores armazenados. Atualmente, os valores continuam armazenados como números decimais sem conversão cambial.
- Testar em execução real a geração de recorrências e os saldos com contas de teste.

## Limites
As alterações foram feitas na cópia de trabalho da Etapa 3. O ZIP original e os bancos de dados de origem foram preservados. Os bancos SQLite não serão incluídos no ZIP distribuível, para evitar compartilhar dados financeiros privados.
