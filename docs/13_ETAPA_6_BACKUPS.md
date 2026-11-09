# 13 — Etapa 6: backups e integridade

## Objetivo

Aumentar a segurança ao verificar e restaurar arquivos de backup.

## Alterações

- Reforçada a verificação dos arquivos com checksum SHA-256.
- Melhorada a validação do conteúdo antes de gravar.
- Reforçados os cuidados transacionais na restauração.
- Incluída proteção contra importar o mesmo backup repetidamente na mesma conta.
- Ampliadas as verificações de integridade do SQLite.

## Validação

25 testes automatizados aprovados, compilação e integridade do ZIP.

## Limitação

SHA-256 ajuda a detectar alterações no arquivo, mas não é assinatura digital e não comprova quem criou o backup.
