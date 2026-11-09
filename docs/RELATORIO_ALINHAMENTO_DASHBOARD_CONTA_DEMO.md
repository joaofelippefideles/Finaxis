# Finaxis — Alinhamento do dashboard e conta de demonstração

## Ajustes solicitados

### 1. Indicadores financeiros alinhados
- Os quatro indicadores foram substituídos por cartões com altura fixa.
- Rótulos e valores usam a mesma estrutura vertical e alinhamento.
- Os valores usam algarismos tabulares e não quebram em duas linhas.
- O CSS acompanha os temas claro e escuro.

### 2. Gráfico de despesas por categoria
- Removidos os 180 raios desenhados manualmente em coordenadas relativas ao gráfico, que podiam ficar ovais/descentralizados conforme a proporção da tela.
- Criado um aro externo dourado concêntrico usando uma segunda pizza do Plotly.
- O aro e a rosca principal compartilham o mesmo centro e são renderizados pela geometria circular nativa do Plotly.

### 3. Erro anterior das tabelas
- Removido o argumento `theme` que causava `TypeError: ArrowMixin.dataframe() got an unexpected keyword argument 'theme'`.
- Como as tabelas são apenas para visualização, passaram a usar `st.table`, permitindo aplicar o CSS às células e cabeçalhos.
- A função auxiliar preserva o uso do DataFrame e remove o índice quando solicitado.

### 4. Conta de administrador para demonstração
- Criada automaticamente na inicialização, apenas se ainda não existir:
  - E-mail: `admin@finaxis.demo`
  - Senha inicial: definida na versão de demonstração anterior; não é exibida no aplicativo.
  - Perfil: `admin`
- A senha é armazenada com PBKDF2-HMAC-SHA256, salt aleatório de 16 bytes e 310.000 iterações.
- A criação é idempotente: inicializações seguintes não recriam a conta nem redefinem a senha.
- A coluna `role` é adicionada automaticamente a bancos existentes, preservando os usuários atuais.

**Limite funcional:** o perfil admin é identificado no banco e na interface, mas esta versão ainda não possui painel administrativo nem regras de autorização exclusivas para operações administrativas globais.

## Testes
- 28 testes automatizados aprovados.
- Teste confirma que a conta demo autentica.
- Teste confirma que o hash não é igual à senha em texto e que a verificação PBKDF2 funciona.
- Teste confirma que nova inicialização não altera o hash existente.
- `py_compile app.py database.py`: aprovado.
- ZIP validado.
- Nenhum banco de dados pessoal incluído.

## Instalação e migração
1. Faça backup da pasta atual e do arquivo `data/finaxis_v2.db`.
2. Extraia o pacote em uma pasta nova.
3. Copie o banco atual para `data/finaxis_v2.db` na nova pasta.
4. Execute `INICIAR_FINAXIS.bat` na raiz do projeto.
5. A coluna `role` e a conta de demonstração serão criadas automaticamente sem apagar os registros existentes.

Troque a senha da conta de demonstração antes de utilizar dados reais ou disponibilizar a aplicação a outras pessoas.
