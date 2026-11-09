# Finaxis — Sistema de Controle Financeiro Pessoal

Segunda versão independente da Entrega 1, desenvolvida em Python, Streamlit e SQLite. O projeto original não é alterado.

## Funcionalidades

1. Dashboard com indicadores, comparativo mensal, gráficos de categorias e evolução.
2. Lançamentos com filtros, pesquisa, edição e exclusão.
3. Contas e transferências entre contas.
4. Cartões de crédito, compras parceladas e acompanhamento do limite cadastrado.
5. Orçamentos mensais por categoria com indicadores de utilização.
6. Contas a pagar e a receber por meio dos lançamentos e seus status.
7. Lançamentos recorrentes (diário, semanal, mensal e anual).
8. Relatórios com exportação CSV, XLSX e PDF.
9. Notificações para despesas pendentes próximas do vencimento, atrasadas e orçamento a partir de 80%.
10. Cadastro/login com hash PBKDF2 de senha e dados separados por usuário.
11. Backup JSON por usuário e rotina de migração da base da versão 1.
12. Interface Streamlit responsiva e navegação por módulos.
13. Perfil, moeda, categorias, validações, estrutura modular e persistência SQLite.

## Requisitos

- Python 3.10+
- Windows, Linux ou macOS
- Dependências listadas em `requirements.txt`

## Executar no Windows

Abra o PowerShell na raiz do projeto (pasta que contém `app.py`):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Se a política do PowerShell impedir a ativação do ambiente virtual, execute diretamente:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Executar no Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`.

## Primeiro acesso

1. Clique em **Criar conta**.
2. Informe nome, e-mail e senha com pelo menos 10 caracteres.
3. Entre no sistema e confira as contas e categorias iniciais.
4. Para importar os lançamentos da versão anterior, entre em **Configurações** e use **Verificar e migrar dados da versão 1**.

A migração é vinculada ao usuário autenticado e pode ser executada uma única vez por usuário. O arquivo original `financeiro.db` não é alterado; uma cópia foi incluída em `data/financeiro_v1.db` como origem de migração. Se a base original estiver em outro local, informe seu caminho na tela de configurações.

## Banco e privacidade

- O banco da V2 fica em `data/finaxis_v2.db`.
- A base antiga para migração fica em `data/financeiro_v1.db`.
- Pode definir `FINAXIS_DB` para escolher o arquivo do banco V2.
- Pode definir `FINAXIS_V1_DB` para escolher a base legada.
- Consultas e alterações dos módulos filtram os registros pelo ID do usuário autenticado.
- Senhas não são guardadas em texto puro.
- O backup JSON exporta somente os registros do usuário autenticado.

**Importante:** SQLite local é apropriado para uso pessoal ou implantação pequena. Para uso público/multiusuário na internet, publique apenas atrás de HTTPS, com controle de acesso e política de backup; não exponha o servidor de desenvolvimento Streamlit diretamente à internet.

## Estrutura

```text
Finaxis_2.0/
├── app.py
├── database.py
├── requirements.txt
├── .streamlit/config.toml
├── docs/
│   ├── README.md
│   └── (demais relatórios e documentação .md)
└── data/
    ├── .gitkeep
    └── financeiro_v1.db
```

## Limitações conhecidas / próximos refinamentos

- Compras no cartão são registradas no módulo de cartões e não são lançadas automaticamente nas despesas, para evitar dupla contagem. O cálculo de ciclo/fatura por competência pode ser refinado em uma próxima revisão.
- A geração de recorrências ocorre ao abrir a aplicação. Em instalações que precisam de execução pontual mesmo quando ninguém abre o sistema, recomenda-se um agendador.
- A restauração JSON já está disponível em Configurações; ela adiciona registros ao usuário atual e deve ser testada primeiro com uma conta de teste para evitar duplicidades.
- O cadastro de usuário está aberto para o ambiente local. Em uma implantação compartilhada/publicada, convém restringir o cadastro ou adicionar aprovação administrativa.

## Revisão técnica — Fase 3

A revisão da Fase 3 reforçou a camada financeira e a migração:

- Transferências agora são gravadas atomicamente, evitando registrar apenas a saída ou apenas a entrada.
- Valores monetários usam `Decimal`; totais de orçamento somam valores decimais sem depender de `SUM(CAST(... AS REAL))`.
- A edição valida conta/categoria pertencentes ao usuário; transferências pareadas são editadas em conjunto e não podem ser alteradas se o par estiver incompleto.
- Compras de cartão são distribuídas por fatura a partir do dia de fechamento; a divisão de parcelas distribui os centavos restantes sem perder valor.
- Faturas exibem total, vencimento, pagamentos e saldo em aberto. Pagamentos parciais registram a saída na conta escolhida e atualizam a fatura; excluir o lançamento de pagamento estorna a baixa da fatura.
- Recorrências validam conta/categoria, tratam datas de fim de mês/ano bissexto e possuem índice de unicidade para evitar gerar a mesma ocorrência duas vezes.
- Migração abre a base V1 em modo somente leitura e realiza as importações dentro de uma transação, sem modificar o banco de origem.
- Backup/restauração contempla pagamentos de faturas e reconstitui seus vínculos com os lançamentos restaurados.

### Testes executados nesta revisão

`python -m unittest discover -s tests -v` — **10 testes aprovados**, cobrindo autenticação e isolamento, transferência atômica, edição/exclusão, backup/restauração, formato monetário brasileiro, fatura parcelada e pagamento parcial, recorrências sem duplicidade, orçamentos decimais e migração somente leitura.

`python -m compileall -q .` — compilação sintática do código Python aprovada.

### Limites ainda conhecidos

- A interface Streamlit não foi iniciada visualmente neste ambiente porque a dependência Streamlit não está instalada aqui. Execute os comandos de instalação acima e valide os fluxos no navegador antes de usar com dados reais.
- O arquivo de banco legado incluído na Entrega 1 contém 11 categorias e zero lançamentos. Se a base real estiver em outro caminho, indique esse caminho na tela de migração e confira os totais antes de usar o sistema.
- O cálculo de fatura usa mês de fechamento como competência e vencimento no mês seguinte. Confirme se esse comportamento corresponde às regras do emissor do seu cartão.
- O cadastro segue aberto para uso local. Antes de disponibilizar a aplicação a terceiros ou na internet, implemente controle de cadastro, HTTPS e uma política de backup operacional.


## Fase 4 — Segurança, interface, relatórios e notificações

Nesta revisão foram adicionados: bloqueio temporário após cinco tentativas inválidas de autenticação (15 minutos), expiração da sessão após 30 minutos sem atividade detectada em uma nova interação, registro de eventos relevantes da conta, consulta do histórico de atividade, opção para marcar todas as notificações como lidas, filtros adicionais nos relatórios e totais calculados com `Decimal`.

Os backups agora identificam o produto e a versão do esquema, limitam o arquivo de restauração a 20 MB e rejeitam arquivos JSON de outro produto. A restauração continua sendo uma operação de adição/mesclagem por nome, portanto deve ser feita preferencialmente em uma conta vazia e após baixar um backup atual.

### Testes

Execute `python -m unittest discover -s tests -v`. A suíte desta entrega contém 13 testes. A validação de sintaxe pode ser feita com `python -m py_compile app.py database.py`.

### Observação de segurança

O controle de sessão de 30 minutos é aplicado quando o Streamlit executa uma nova interação; não há temporizador de servidor que encerre uma conexão ociosa exatamente no minuto 30. Para publicação multiusuário na internet, recomenda-se HTTPS, proxy reverso, gestão segura de segredos e revisão operacional adicional.


## Conta de demonstração (administrador)

A inicialização cria automaticamente, uma única vez, a conta:

- E-mail: `admin@finaxis.demo`
- Perfil salvo: `admin`

A senha da conta não é exibida na tela de login nem neste documento. Ela é
armazenada no SQLite como hash PBKDF2-HMAC-SHA256 com salt aleatório
(310.000 iterações); o texto da senha não é gravado no banco. Configure/troque
a senha antes de usar a aplicação com dados reais ou expô-la à rede.

O perfil `admin` identifica a conta de demonstração. Esta versão ainda não
implementa um painel administrativo nem permissões adicionais de gestão global.
