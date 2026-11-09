# Finaxis — Remoção da senha visível e atualização da marca

## Alterações realizadas
- Removido da tela de login o aviso que exibia e-mail e senha da demonstração.
- Removida a senha em texto puro do código-fonte: a conta de demonstração usa um hash PBKDF2-HMAC-SHA256 pré-calculado, com salt aleatório e 310.000 iterações.
- Mantida a conta de demonstração `admin@finaxis.demo`; o processo de inicialização continua idempotente.
- Atualizado o nome exibido no navegador, cabeçalho da aplicação, barra lateral, relatórios e inicializador para **Finaxis**.
- Atualizados os títulos dos documentos do projeto para Finaxis.
- Preservado o identificador interno `Finaxis 2.0` usado no formato de backup, para não invalidar backups antigos.

## Segurança e observações
A senha não aparece mais na tela de login, no README ou em texto puro no código. O hash não permite recuperar diretamente a senha original. Como a senha inicial já foi informada anteriormente ao proprietário do projeto, ela continua sendo a credencial inicial da conta de demonstração. Altere-a antes de utilizar dados reais ou expor a aplicação.

## Validação
- Testes automatizados e compilação executados após as alterações.
- ZIP verificado.
- Nenhum banco de dados pessoal incluído.
