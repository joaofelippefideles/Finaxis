# 17 — Conta de demonstração

## Objetivo

Criar uma conta de demonstração para permitir visualizar o sistema sem precisar cadastrar uma conta do zero.

## Alteração de segurança

Foi solicitado que a senha não ficasse armazenada em texto puro. A conta de demonstração foi configurada com hash PBKDF2-HMAC-SHA256, salt aleatório e 310.000 iterações.

## Tela de login

O aviso que exibia o e-mail e a senha da demonstração foi removido da tela. A senha em texto puro também foi removida dos arquivos distribuídos.

## Observação importante

A conta é identificada como `admin`, mas isso não deve ser interpretado como confirmação de que existe um painel global completo de administração ou um sistema avançado de permissões. A credencial inicial deve ser alterada antes de utilizar dados reais ou disponibilizar o sistema.
