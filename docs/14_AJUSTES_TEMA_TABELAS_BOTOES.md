# 14 — Ajustes posteriores: tema escuro, tabelas e botões

## O que apareceu durante o uso

Depois das etapas de interface, foram enviadas capturas mostrando que algumas tabelas continuavam claras no tema escuro e que certos botões tinham texto difícil de ler.

## Erro de compatibilidade identificado

Uma captura mostrou o erro:

`TypeError: ArrowMixin.dataframe() got an unexpected keyword argument 'theme'`

A chamada de `st.dataframe` estava recebendo um argumento `theme` que não era aceito pela versão do Streamlit instalada naquele ambiente.

## Correção

A função auxiliar de exibição de tabelas foi adaptada para não repassar esse argumento incompatível. Também foram feitos ajustes de CSS para melhorar contraste de tabelas, botões, campos e mensagens.

## Resultado esperado

Tabelas e controles devem manter leitura adequada nos temas claro e escuro.

## Validação

A correção foi guiada pelo erro real apresentado na tela. A homologação final deve conferir todas as páginas e todos os tipos de tabela no navegador.
