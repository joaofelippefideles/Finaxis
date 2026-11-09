# 03 — Arquitetura e estrutura técnica

## Tecnologias

A estrutura técnica do Finaxis foi baseada em:

- **Python:** linguagem da aplicação e das regras de negócio.
- **Streamlit:** interface acessada pelo navegador.
- **SQLite:** banco de dados local.
- **`app.py`:** aplicação, navegação e interface.
- **`database.py`:** persistência, consultas e regras ligadas ao banco.
- **Testes automatizados:** verificação de operações e regras.

## Organização

A separação entre interface e operações de banco ajudou a manter o projeto mais compreensível e facilitou testar funções sem depender de executar manualmente cada tela.

## Execução

Durante o desenvolvimento, a aplicação foi executada localmente pelo Streamlit, no navegador, usando endereços locais como `localhost`.

Mais tarde, foi criado um inicializador para Windows, documentado separadamente em `16_INICIALIZADOR_WINDOWS.md`.

## Distribuição

Os pacotes de entrega foram preparados sem ambientes virtuais, caches e bancos financeiros pessoais. Isso reduz o tamanho do pacote e evita distribuir dados privados junto com o código.
