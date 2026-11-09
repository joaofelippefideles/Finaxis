# 02 — Planejamento do Finaxis 2.0

## Por que surgiu uma nova versão

Com a primeira entrega como ponto de partida, foi definida a evolução do sistema para uma segunda versão, inicialmente chamada **Finaxis 2.0**.

A intenção era ampliar o projeto sem perder o que já havia sido construído. A nova versão deveria oferecer uma estrutura mais completa, com usuários, dados separados e mais recursos de controle financeiro.

## Requisitos registrados

- Desenvolver em Python.
- Utilizar Streamlit como interface.
- Utilizar SQLite para persistência local.
- Implementar login.
- Separar os dados por usuário.
- Preservar e migrar os dados compatíveis da versão 1.
- Evoluir os módulos financeiros existentes.
- Organizar o trabalho em fases e validar as alterações.

Foi mencionado um escopo de 13 melhorias propostas. Entretanto, a lista literal completa dessas 13 melhorias não está preservada no histórico disponível. Este documento não tenta reconstruí-la por suposição.

## Decisões importantes

A evolução seria incremental. A versão anterior não deveria ser sobrescrita e a migração teria que ocorrer para o usuário autenticado, mantendo a origem intacta.

## Resultado do planejamento

O projeto passou a ter uma direção clara: sair de uma primeira entrega de controle financeiro e evoluir para uma aplicação local multiusuário, com módulos financeiros mais completos e cuidados maiores com segurança e integridade.
