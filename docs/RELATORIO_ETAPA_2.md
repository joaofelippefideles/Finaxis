# Finaxis — Relatório da Etapa 2: Correções de segurança

## Alterações implementadas
1. **Bloqueio de login:** após 5 falhas consecutivas, a conta/e-mail fica bloqueada por 15 minutos. Ao expirar, o contador é reiniciado. Tentativas fora da janela de 15 minutos também deixam de acumular.
2. **Troca de senha:** a validação foi centralizada em `database.change_password`; exige senha atual correta e aplica o mínimo de 10 caracteres pela função de hash existente. A alteração é registrada na auditoria.
3. **Restauração de backup:** agora exige `produto = Finaxis`, `schema_version = 2`, coleções obrigatórias em formato de lista, valida coleções opcionais e limita o total a 100.000 registros, além do limite existente de 20 MB. A operação permanece dentro da transação SQLite, com rollback em caso de erro.
4. **Testes de regressão:** adicionados testes para expiração do bloqueio, troca de senha e rejeição de versão incompatível do backup.

## Validação executada
- `python -m unittest discover -s tests -v`: **16 testes aprovados**.
- `python -m py_compile app.py database.py`: **aprovado**.
- Testes executados em banco temporário; os bancos financeiros existentes não foram usados como alvo de escrita.
- Não foi realizada validação visual no navegador/Streamlit nesta etapa.

## Pontos ainda pendentes de segurança
- A expiração de sessão é verificada quando o Streamlit executa uma nova interação/rerun; não é um temporizador independente no servidor.
- O bloqueio atual é por e-mail, não por endereço IP. Em implantação pública, recomenda-se acrescentar limitação por IP/proxy reverso e monitoramento.
- A revisão de isolamento foi coberta pelos testes existentes e permanece como requisito para auditoria de cada nova consulta/ação nas próximas etapas.
- A restauração é aditiva e pode criar duplicidades de registros; a interface já solicita confirmação. Recomenda-se backup antes de restaurar.

## Limites desta etapa
As alterações foram feitas somente na cópia de trabalho. O ZIP original e os bancos originais foram preservados. Esta etapa não cobre ainda correções financeiras, relatórios, interface ou validação de implantação.
