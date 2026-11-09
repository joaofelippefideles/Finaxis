# 09 — Etapa 2: correções de segurança

## Objetivo

Corrigir comportamentos do login e reforçar a validação de backups.

## Alterações

- Ajustado o bloqueio temporário após falhas de login.
- Falhas antigas deixam de permanecer na contagem depois que a janela expira.
- A contagem é limpa quando o bloqueio termina.
- A troca de senha exige a senha atual.
- A validação do backup confere produto, versão do esquema e estrutura das coleções.
- Foram definidos limites para a quantidade de registros processados.
- Foram adicionados testes para bloqueio expirado, troca de senha e versão incompatível de backup.

## Validação

16 testes automatizados aprovados e compilação sem erros.

## Limitações registradas

O bloqueio é por conta/e-mail, não por IP. A expiração de sessão depende dos ciclos de interação do Streamlit. A restauração aditiva foi tratada posteriormente na Etapa 6.
