# 05 — Migração dos dados da versão 1

## Objetivo

A migração foi planejada para aproveitar os dados compatíveis da Entrega 1 no Finaxis 2.0, sem apagar nem alterar o banco antigo.

## Como foi pensada

A tela de configurações apresenta uma área para informar o caminho do banco antigo e verificar/migrar os dados para o usuário autenticado.

A operação deve ser executada com cuidado e, conforme a orientação apresentada na aplicação, uma única vez.

## Preservação da origem

A proposta é importar os registros compatíveis sem usar o banco antigo como destino de gravação. Dessa forma, o banco original permanece preservado.

## O que foi possível verificar

O banco antigo disponibilizado para análise continha 11 categorias e nenhum lançamento financeiro.

Isso permitiu verificar parte do formato, mas não comprova o comportamento completo com uma base que tenha muitas movimentações, contas ou outros registros.

## Homologação recomendada

Antes de considerar a migração encerrada:
1. fazer uma cópia do banco antigo;
2. testar a migração com essa cópia;
3. conferir quantidades e valores;
4. verificar categorias e lançamentos;
5. confirmar que o banco de origem não foi alterado.

Não utilize o único exemplar do banco antigo como ambiente de teste.
