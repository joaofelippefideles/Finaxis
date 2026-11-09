# 08 — Etapa 1: preparação e proteção

## Objetivo

Preparar uma área de trabalho segura antes de começar as correções.

## Alterações

- Foi criada uma cópia independente a partir da Entrega 4.
- O pacote original foi preservado em um backup separado.
- Ambientes virtuais, caches e arquivos temporários foram retirados da cópia de distribuição.
- Os bancos foram preservados na área de trabalho, mas excluídos dos ZIPs distribuídos.
- Foi criado um manifesto SHA-256.
- O ZIP foi verificado.

## Validação

13 testes automatizados aprovados. `app.py` e `database.py` compilados sem erros.

## Resultado

A equipe passou a trabalhar em uma cópia protegida, mantendo o original intacto.
