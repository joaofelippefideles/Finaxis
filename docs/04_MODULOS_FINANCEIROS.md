# 04 — Módulos e funcionalidades financeiras

Este documento registra as áreas funcionais que foram desenvolvidas ou revisadas durante a evolução do Finaxis. O histórico confirma as áreas abaixo, mas não fornece uma especificação completa de todos os campos e regras de cada tela.

## Usuários e autenticação

A aplicação passou a contar com login e associação dos dados ao usuário autenticado. A separação por usuário é uma regra central: cada conta deve trabalhar com seus próprios registros.

As senhas são armazenadas como hashes, não como texto puro.

## Lançamentos

O sistema trabalha com receitas e despesas, com informações de data, descrição, categoria, conta, valor, situação e observações.

## Contas e transferências

Foram trabalhadas operações de contas e transferências. A transferência precisa registrar os dois lados da movimentação de forma consistente.

## Cartões de crédito

A aplicação contempla cartões, parcelamentos e pagamentos de fatura. As regras de fechamento e competência exigem validação com exemplos dos emissores usados pelo usuário.

## Orçamentos

O sistema contempla acompanhamento de limites de gastos por categoria.

## Recorrências

O sistema permite programar movimentações recorrentes. As datas mensais e anuais receberam correções específicas na Etapa 3.

## Relatórios e notificações

Foram desenvolvidas áreas de relatórios e notificações, revisadas posteriormente para melhorar filtros, apresentação e exportação.

## Backup e restauração

A aplicação oferece recursos de exportação e restauração de dados, que foram reforçados na Etapa 6.
