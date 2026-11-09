# Finaxis — Relatório da Etapa 6

## Objetivo
Reforçar a proteção dos backups, a restauração dos dados e a verificação da integridade do SQLite.

## Alterações realizadas

1. **Checksum SHA-256:** os novos backups JSON recebem `integrity_sha256`, calculado sobre o conteúdo do backup. A restauração verifica o checksum antes de gravar os dados.
2. **Compatibilidade:** backups Finaxis schema 2 sem checksum continuam aceitos, para preservar arquivos antigos. Esses arquivos passam pelas validações estruturais e de campos disponíveis.
3. **Validação antecipada:** verifica tamanho máximo, versão, coleções obrigatórias/opcionais, formato dos registros, tipo/descrição, valores e datas dos lançamentos e dados essenciais de contas/categorias.
4. **Restauração atômica:** os registros são importados em uma transação. Se ocorrer uma falha durante a importação, o SQLite desfaz as alterações dessa operação.
5. **Proteção contra reimportação:** cada backup é identificado por fingerprint SHA-256 e registrado por usuário. A tentativa de importar o mesmo arquivo novamente na mesma conta é recusada sem duplicar os dados.
6. **Integridade SQLite:** nova verificação com `PRAGMA integrity_check` e `PRAGMA foreign_key_check`, exibida na área Configurações.
7. **Transparência:** a tela mostra o resultado da verificação e a quantidade de registros por coleção para a conta autenticada.
8. **Confirmação de restauração:** texto da interface atualizado para orientar a criação de backup atual antes da importação.

## Arquivos alterados
- `database.py`
- `app.py`
- `tests/test_database.py`

## Validação
- Testes automatizados: **25 aprovados**.
- Compilação (`py_compile app.py database.py`): aprovada.
- Integridade do ZIP: verificada.
- Teste de checksum adulterado: aprovado (restauração bloqueada).
- Teste de reimportação do mesmo backup: aprovado (não duplica).
- Teste de compatibilidade com backup schema 2 sem checksum: aprovado.
- Testes executados em banco temporário; nenhum banco financeiro pessoal foi usado como alvo.

## Limitações e cuidados
- O checksum detecta alteração acidental ou adulteração do arquivo, mas não é assinatura digital: alguém que modifique o conteúdo e recalcule o SHA-256 também pode gerar um checksum válido. Para autenticidade criptográfica seria necessária assinatura com chave protegida.
- Backups antigos sem checksum são aceitos por compatibilidade e, portanto, não têm verificação criptográfica de integridade.
- A restauração continua sendo uma importação conciliada por nomes, não uma substituição completa da conta. Categorias/contas são conciliadas e algumas configurações podem ser atualizadas; lançamentos são adicionados.
- A verificação SQLite é estrutural/referencial; não substitui cópia externa, teste periódico de restauração nem política de retenção.
- Ainda falta validação visual no navegador e teste operacional com cópia de um banco real. Não testar restauração em cima do banco original sem antes criar cópia independente.

## Base
Derivado de `Finaxis_2.0_Etapa5_Correcoes_Relatorios_Exportacoes.zip`. O ZIP de origem e os bancos pessoais originais foram preservados.
