# Relatório — Etapa 1: Preparação e proteção

## Escopo realizado
- Preservada uma cópia exata do ZIP original recebido.
- Extraída uma cópia independente para trabalho.
- Mantidos os bancos SQLite da Entrega 4 na cópia de trabalho, sem alterações intencionais.
- Excluídos da cópia de trabalho os ambientes virtuais (`.venv`), caches e arquivos compilados.
- Gerado manifesto com SHA-256 dos arquivos copiados e do ZIP original.

## Validações
- Integridade do ZIP original: OK.
- Integridade do pacote de trabalho: OK.
- `python -m unittest discover -s tests -v`: 13 testes aprovados.
- `python -m py_compile app.py database.py`: aprovado.

## Observações
- Os testes foram executados no diretório isolado de trabalho. A suíte utiliza banco temporário para os testes; os arquivos SQLite do projeto foram preservados.
- A compilação/testes foram executados no ambiente desta análise, não no Windows do usuário.
- A interface Streamlit não foi iniciada nesta etapa.
- A pasta `.venv` original não foi copiada para a área de trabalho; ela permanece dentro do backup exato do ZIP original.
- Os bancos `data/finaxis_v2.db` e `data/financeiro_v1.db` contêm dados e devem ser tratados como privados.
- Esta etapa não altera código de produção nem corrige os problemas identificados na análise. Ela apenas prepara e protege a base para as próximas etapas.

## Próxima etapa
Etapa 2 — Correções de segurança, sempre sobre `projeto_trabalho/`, com novos backups antes de alterações.
