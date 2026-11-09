# 16 — Inicializador do Windows

## Pedido

Foi solicitado um jeito de executar o Finaxis sem precisar digitar repetidamente comandos no terminal, apenas para abrir a aplicação e conferir se estava funcionando.

## Alteração

Foi criado o arquivo `INICIAR_FINAXIS.bat`.

A proposta do inicializador é:
- preparar o ambiente Python local;
- instalar dependências quando necessário;
- reutilizar o ambiente preparado nas próximas execuções;
- iniciar a aplicação Streamlit;
- permitir que o usuário abra o sistema com duplo clique.

## Observação

A primeira execução pode demorar mais porque precisa preparar o ambiente e instalar dependências. As execuções seguintes devem ser mais rápidas, desde que as dependências não precisem ser atualizadas.
