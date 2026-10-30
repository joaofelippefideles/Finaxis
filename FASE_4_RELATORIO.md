# Finaxis 2.0 — Relatório da Fase 4

## Escopo implementado

### Segurança e isolamento
- Limitação de tentativas de login: cinco falhas consecutivas geram bloqueio temporário de 15 minutos por e-mail.
- Sessão autenticada expira após 30 minutos de inatividade detectada na próxima interação do Streamlit.
- Registro de eventos de conta: login, logout, cadastro, alteração de perfil, alteração de senha e restauração de backup.
- Consulta do histórico recente de atividade na tela Configurações.
- Operações de notificação e auditoria limitadas ao `user_id` autenticado.

### Relatórios e interface
- Relatórios ganharam filtros por tipo, categoria e conta, além do intervalo de datas.
- Totais de relatório calculados com `Decimal`, separando despesas pagas e pendentes e exibindo resultado realizado.
- Central de notificações mostra contagem de não lidas e permite marcar todas como lidas.
- Interface informa o prazo de inatividade configurado.

### Backup e restauração
- Backup exportado com identificação do produto e versão do esquema.
- Restauração limita arquivos a 20 MB e valida o produto/formato antes de importar.
- Mantida a exportação de dados somente do usuário selecionado.

## Validação executada

- `python -m unittest discover -s tests -v`: **13 testes aprovados**.
- `python -m py_compile app.py database.py`: **aprovado**.
- Testes adicionais cobrem bloqueio/limpeza de tentativas, trilha de auditoria, isolamento ao marcar notificações e validação de backup.

## Pendências e limites conhecidos

1. Streamlit não está instalado neste ambiente, portanto a interface não foi iniciada em navegador nesta execução. Instale `requirements.txt` e valide visualmente em Windows.
2. O timeout é verificado em reruns/interações do Streamlit; não é um mecanismo de expiração em tempo real no servidor.
3. O bloqueio de login é baseado em e-mail no banco local SQLite. Para implantação pública ou com múltiplas instâncias, recomenda-se rate limiting também no proxy/servidor e controles operacionais adicionais.
4. A trilha de auditoria registra eventos da conta, mas não é um log imutável contra um administrador com acesso direto ao arquivo SQLite.
5. Backup restaurado é mesclado por nomes e adiciona lançamentos; usar conta vazia ou validar cuidadosamente para evitar duplicidades.
6. Notificações atuais dependem das datas dos lançamentos pendentes como datas de vencimento; não há envio externo por e-mail/SMS.

## Conclusão

A implementação da Fase 4 foi concluída no código e passou pela suíte automatizada. A aprovação final da fase depende da validação visual do Streamlit e do teste de instalação em ambiente Windows limpo. A Fase 5 deverá executar os testes integrados e corrigir eventuais problemas encontrados.
