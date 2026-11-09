# Análise dos conceitos de Python no Finaxis

## Parte 1 — Introdução

Este documento relaciona os 15 módulos teóricos dos Temas 2 a 5 da disciplina de Paradigmas de Linguagens de Programação em Python com evidências concretas no código do Finaxis. O objetivo é demonstrar onde cada conceito aparece, como ele é aplicado e, quando for o caso, registrar que determinado recurso não foi utilizado ou aparece apenas de forma parcial.

O Finaxis é uma aplicação financeira composta por uma interface web em Streamlit (`app.py`), uma camada de persistência e regras de negócio em SQLite (`database.py`) e uma suíte de testes automatizados (`tests/test_database.py`). A análise priorizou os arquivos Python do projeto. Arquivos de configuração, documentação, banco de dados e dependências externas foram consultados apenas como apoio.

A inserção de comentários e docstrings seguiu três regras:

1. Não alterar lógica, nomes, arquitetura, banco de dados, bibliotecas ou funcionalidades.
2. Explicar o conceito no ponto exato em que ele aparece no código.
3. Não atribuir ao projeto conceitos que não existem ou que existem apenas de forma indireta.

Os comentários usam marcadores como `# CONCEITO: ...` para facilitar a leitura didática. As docstrings foram ampliadas em funções, classes e métodos relevantes, sem mudar assinaturas, retornos ou efeitos colaterais.

---

## Parte 2 — Os 15 módulos teóricos e sua aplicação no Finaxis

### Tema 2 — Fundamentos das linguagens

#### 1. Classificação das linguagens

**Onde aparece:** `app.py`, `database.py` e `tests/test_database.py`.

Python é utilizada como uma linguagem de alto nível, interpretada, dinamicamente tipada e multiparadigma. O código não declara tipos de variáveis e não exige compilação prévia separada: os arquivos são executados pelo interpretador CPython. A aplicação também usa módulos e bibliotecas externas, o que caracteriza uma linguagem de propósito geral com forte ecossistema.

**Evidências:**

- `app.py` executa comandos de interface diretamente no nível do módulo, comportamento típico de um script interpretado.
- Variáveis como `uid`, `u`, `rows`, `df` e `page` recebem valores de tipos diferentes sem anotação explícita.
- O projeto usa `from __future__ import annotations`, mas não há verificação estática obrigatória nem anotações de tipo sistemáticas.
- A execução do Streamlit reexecuta o script a cada evento, o que reforça o modelo interpretado e orientado a eventos.

**Classificação:** conceito contextual, não é uma instrução isolada da linguagem. A evidência está no modo como o projeto é escrito e executado.

#### 2. Critérios de avaliação de linguagens

**Onde aparece:** principalmente em `database.py` e `tests/test_database.py`.

Não existe um trecho de código que “implemente” critérios de avaliação. O que existe são decisões de projeto que podem ser avaliadas por esses critérios:

- **Legibilidade:** nomes descritivos (`list_transactions`, `add_budget`, `card_outstanding`), separação entre interface e banco, funções curtas e docstrings.
- **Confiabilidade:** uso de `Decimal` para dinheiro, transações com commit/rollback em `conn()`, hashes PBKDF2 para senhas, validação de backups e 28 testes automatizados.
- **Custo:** uso da biblioteca padrão e de SQLite, sem servidor de banco externo; dependências externas limitadas a Streamlit, pandas, Plotly, openpyxl e reportlab.
- **Portabilidade:** execução em Windows e em outros sistemas com Python instalado; caminhos construídos com `pathlib.Path`.
- **Manutenibilidade:** módulos separados, funções reutilizáveis e testes que isolam o banco temporário.

**Classificação:** conceito contextual e avaliativo. Não deve ser tratado como recurso sintático.

#### 3. Paradigmas de linguagens

**Onde aparece:** os três arquivos Python.

O Finaxis é predominantemente **procedimental/imperativo**, pois organiza a solução em funções e comandos sequenciais. Também apresenta elementos do paradigma **funcional** e usa **orientação a objetos** por meio de bibliotecas e da classe de testes.

- **Procedimental/imperativo:** `database.py` possui 56 funções de domínio; `app.py` executa a interface de cima para baixo e usa `if/elif` para selecionar páginas.
- **Funcional:** funções de ordem superior (`notify_error(fn)`), lambdas (`lambda: db.create_user(...)`), compreensões de lista, expressões geradoras e `sum(...)`.
- **Orientado a objetos:** objetos de `pandas.DataFrame`, `plotly.graph_objects.Figure`, `pathlib.Path`, `decimal.Decimal`, `datetime.date`, conexões SQLite e a classe `DatabaseTests`.
- **Declarativo/lógico:** não foi identificado. As consultas SQL são declarativas, mas o projeto não usa Prolog, regras lógicas ou um paradigma declarativo implementado em Python.

**Classificação:** multiparadigma na prática, com predominância procedimental.

#### 4. Métodos de implementação

**Onde aparece:** execução geral do projeto e uso de bibliotecas.

O projeto é executado pelo interpretador CPython. Não há etapa de compilação própria, geração de executável nativo, JIT ou checagem estática obrigatória. O Streamlit atua como framework de execução: o script é interpretado e reexecutado a cada interação. Bibliotecas como pandas e SQLite possuem partes implementadas em C, mas são acessadas pela API Python.

**Evidências:**

- `st.set_page_config(...)` e os comandos de interface são executados no nível do módulo.
- `db.init_db()` é chamado na inicialização.
- O fluxo depende de `st.rerun()` após eventos.
- Não há `setup.py` de compilação, `pyproject.toml` com build nativo ou uso explícito de `compileall`/Cython/Numba.

**Classificação:** interpretação evidente; compilação/JIT não identificados. O uso de bibliotecas nativas é indireto.

---

### Tema 3 — A linguagem Python

#### 5. A linguagem Python: sintaxe, semântica e organização

**Onde aparece:** `app.py`, `database.py` e `tests/test_database.py`.

O código demonstra a sintaxe da linguagem: indentação obrigatória, blocos delimitados por dois-pontos, funções, classes, módulos, imports, docstrings, strings multilinha, operadores e expressões. A organização em módulos separa interface, persistência e testes.

**Evidências:**

- `app.py` importa `database as db` e usa funções do módulo.
- `database.py` possui docstring de módulo e constantes `TIPOS` e `STATUS`.
- `tests/test_database.py` importa `unittest` e `database`.
- Blocos `if`, `for`, `try`, `with`, `def` e `class` usam indentação consistente.

**Classificação:** conceito estrutural presente em todo o projeto.

#### 6. Variáveis

**Onde aparece:** os três arquivos.

Há variáveis locais, globais, constantes lógicas e atributos de instância. A linguagem não exige declaração de tipo; o tipo é associado ao valor em tempo de execução.

**Evidências:**

- Globais: `theme_css`, `SESSION_TIMEOUT_MINUTES`, `uid`, `u`, `notifs` em `app.py`.
- Constantes: `TIPOS`, `STATUS`, `DB_PATH` e `LEGACY_DB` em `database.py`.
- Locais: `rows`, `total`, `value`, `payload`, `fingerprint`.
- Atributos de instância: `self.tmp`, `self.old_path`, `self.uid` em `DatabaseTests`.
- Reatribuição: `db.DB_PATH = Path(self.tmp.name) / "test.db"` no `setUp`.

**Classificação:** conceito central e amplamente aplicado.

#### 7. Tipos de dados e expressões

**Onde aparece:** os três arquivos.

O projeto usa tipos simples e compostos:

- `str`, `int`, `float`, `bool`, `None`.
- `list`, `tuple`, `dict`, `set`.
- `bytes` e `bytearray` em backup e downloads.
- `Decimal` para valores monetários.
- `date`, `datetime` e `timedelta` para datas e prazos.
- `Path` para caminhos.
- `DataFrame` para tabelas.
- Objetos de conexão e linhas SQLite.

As expressões incluem aritmética, comparação, operadores lógicos, f-strings, slicing, acesso por índice/chave, chamadas de método, expressões condicionais, compreensões, geradores e `lambda`.

**Evidências:**

- `money()` usa `Decimal`, `quantize` e `ROUND_HALF_UP`.
- `f"{money(v):,.2f}"` usa formatação numérica.
- `x["data"][:7]` usa slicing de string.
- `{row["name"] for row in ...}` usa set comprehension.
- `[dict(r) for r in ...]` usa list comprehension.
- `sum((money(r["valor"]) for r in rows ...), money(0))` usa expressão geradora.
- `st.session_state` é tratado como dicionário.

**Classificação:** conceito central e amplamente aplicado.

#### 8. Atribuição, entrada e saída

**Onde aparece:** principalmente em `app.py` e `database.py`.

**Atribuição:**

- Atribuição simples: `uid = st.session_state.user_id`.
- Atribuição múltipla: `left, right = st.columns([1.2, 1])`.
- Desempacotamento: `for nome, icone in paginas`.
- Atribuição aumentada: `created += cur.rowcount`, `total += amount`.
- Atribuição a atributo: `st.session_state.last_activity = datetime.now()`.

**Entrada:**

- Widgets Streamlit: `st.text_input`, `st.number_input`, `st.date_input`, `st.selectbox`, `st.checkbox`, `st.file_uploader`.
- Parâmetros de funções e valores de formulário.
- Leitura de banco SQLite e de arquivo JSON de backup.

**Saída:**

- `st.write`, `st.markdown`, `st.error`, `st.success`, `st.warning`, `st.table`, `st.metric`, `st.download_button`.
- Exportação CSV, XLSX e PDF.
- Gravação no banco e geração de backup JSON.
- Retornos de funções e dicionários de resultado.

**Classificação:** conceito central e amplamente aplicado.

---

### Tema 4 — Controle, subprogramas, bibliotecas e eventos

#### 9. Estruturas de decisão e repetição

**Onde aparece:** os três arquivos.

**Decisão:**

- `if/elif/else` para selecionar páginas em `app.py`.
- `if` aninhados para validar login, formulários, status e permissões.
- Expressões condicionais (`1 if active else 0`).
- `try/except` para tratamento de exceções.

**Repetição:**

- `for` sobre listas, tuplas, dicionários, linhas do banco e resultados de consultas.
- `while` em `run_recurring` para gerar ocorrências vencidas.
- `range`, `enumerate`, `zip` não identificado, `sorted` e compreensões.
- `any` e `all` em validações de backup e testes.

**Evidências:**

- `for nome, icone in paginas` percorre a navegação.
- `for purchase in rows` e `for index, amount in enumerate(values)` calculam parcelas.
- `while next_due <= today and processed < cap` limita a geração de recorrências.
- `if spent > lim: ... elif spent >= lim * Decimal("0.8"): ...` classifica o orçamento.

**Classificação:** conceito central e amplamente aplicado.

#### 10. Subprogramas

**Onde aparece:** `app.py`, `database.py` e `tests/test_database.py`.

O projeto usa funções como unidade principal de organização. Há parâmetros posicionais, parâmetros nomeados, valores padrão, `**kwargs`, retornos, funções de ordem superior e lambdas.

**Evidências:**

- `database.py` possui 56 funções de domínio, como `money`, `conn`, `create_user`, `add_transaction`, `card_invoice`, `restore_backup` e `migrate_legacy`.
- `app.py` define `money`, `show_dataframe`, `notify_error`, `tx_df` e `tx_form`.
- `show_dataframe(data, **kwargs)` demonstra parâmetros variáveis nomeados.
- `tx_form(prefix, default_tipo="despesa")` demonstra valor padrão.
- `notify_error(fn)` recebe outra função e a executa; é uma função de ordem superior.
- `lambda: db.create_user(...)` é usada para adiar a execução e permitir o tratamento centralizado de exceções.
- `conn()` usa `@contextmanager` e `yield`, transformando uma função geradora em gerenciador de contexto.

**Classificação:** conceito central e amplamente aplicado.

#### 11. Bibliotecas

**Onde aparece:** imports dos três arquivos.

**Biblioteca padrão:**

- `io`, `os`, `shutil`, `tempfile`, `uuid`.
- `datetime`, `decimal`, `pathlib`.
- `contextlib`, `calendar`.
- `sqlite3`, `hashlib`, `hmac`, `secrets`.
- `json`, `csv`.
- `unittest`.

**Bibliotecas externas:**

- `streamlit` (interface e eventos).
- `pandas` (DataFrame e exportação).
- `plotly.express` e `plotly.graph_objects` (gráficos).
- `openpyxl` (exportação Excel).
- `reportlab` (exportação PDF).

**Evidências:**

- `import pandas as pd`, `import plotly.express as px`, `import streamlit as st`.
- `from reportlab.platypus import SimpleDocTemplate, Table, ...` dentro de bloco `try`.
- `with pd.ExcelWriter(excel, engine="openpyxl") as writer:`.
- `sqlite3.connect(...)`, `hashlib.pbkdf2_hmac(...)`, `secrets.token_bytes(...)`.

**Classificação:** conceito central. O projeto reaproveita bibliotecas em vez de reimplementar recursos.

#### 12. Programação orientada a eventos

**Onde aparece:** `app.py`.

O Streamlit é um framework orientado a eventos. Cada clique, envio de formulário, alteração de campo ou upload provoca uma nova execução do script. O estado é preservado em `st.session_state`.

**Evidências:**

- `st.button(...)` retorna verdadeiro no evento de clique.
- `st.form_submit_button(...)` dispara o processamento do formulário.
- `st.download_button(...)`, `st.file_uploader(...)` e `st.checkbox(...)` são componentes interativos.
- `st.rerun()` solicita nova execução após mudança de estado.
- `st.session_state` guarda `user_id`, `last_activity`, `pagina_atual` e chaves de submissão.

**Limitação:** não foram identificados callbacks explícitos `on_change`, `on_click` ou `on_select` definidos pelo projeto. O modelo de eventos existe e é usado, mas a forma predominante é a verificação do retorno dos widgets após a reexecução.

**Classificação:** presente, com aplicação parcial no que se refere a callbacks customizados.

---

### Tema 5 — Orientação a objetos

#### 13. Programação orientada a objetos

**Onde aparece:** de forma limitada em `app.py` e `database.py`; de forma explícita em `tests/test_database.py`.

Não há classes de domínio próprias para `Usuário`, `Conta`, `Transação`, `Cartão` ou `Orçamento`. Esses conceitos são representados por dicionários, listas e tabelas SQLite. A orientação a objetos aparece principalmente no uso de objetos de bibliotecas e na classe de testes.

**Evidências de OOP por bibliotecas:**

- `Path(...)`, `Path.resolve()`, `Path.parent`.
- `Decimal(...)`, `Decimal.quantize()`.
- `date.fromisoformat()`, `datetime.now()`.
- `sqlite3.Connection`, `sqlite3.Row`.
- `pandas.DataFrame`, `DataFrame.groupby()`, `DataFrame.to_csv()`.
- `plotly.graph_objects.Figure`, `Figure.add_trace()`.
- Objetos de página e widgets do Streamlit.

**Classificação:** presente por uso de objetos, mas ausente como modelagem de domínio própria. Portanto, é parcial no contexto didático de OOP.

#### 14. Orientação a objetos em Python

**Onde aparece:** `tests/test_database.py`, classe `DatabaseTests`.

A classe demonstra:

- Definição com `class DatabaseTests(unittest.TestCase):`.
- Herança de `unittest.TestCase`.
- Métodos de instância com `self`.
- Atributos de instância: `self.tmp`, `self.old_path`, `self.old_legacy`, `self.uid`.
- Métodos sobrescritos: `setUp` e `tearDown`.
- Uso de métodos herdados: `assertEqual`, `assertTrue`, `assertIsNotNone`, `assertRaises`.
- Ciclo de vida controlado pelo framework de testes.

Não foram identificados no projeto:

- `__init__` próprio.
- `@dataclass`.
- Propriedades (`@property`).
- Métodos de classe (`@classmethod`) ou estáticos (`@staticmethod`).
- Classes abstratas próprias.
- Sobrecarga de operadores.
- Metaclasses ou descritores.

**Classificação:** presente e explícita na classe de testes; não é usada como arquitetura principal da aplicação.

#### 15. Herança e polimorfismo

**Onde aparece:** `tests/test_database.py` e no uso de bibliotecas.

**Herança:**

- `DatabaseTests` herda de `unittest.TestCase`.
- `setUp` e `tearDown` sobrescrevem métodos previstos pela classe base.
- Os métodos de asserção são herdados e reutilizados.

**Polimorfismo:**

- O `unittest` chama `setUp` e `tearDown` por meio do contrato da classe base, mas executa as versões definidas em `DatabaseTests`. Isso é polimorfismo por sobrescrita.
- Objetos diferentes respondem a métodos de mesmo nome: `to_csv` em DataFrame, `getvalue` em buffer de arquivo, `resolve` em Path.
- Não há hierarquia própria com múltiplas subclasses, classes abstratas, interfaces ou métodos genéricos.

**Classificação:** herança presente e polimorfismo parcial. A aplicação não usa polimorfismo como recurso central de modelagem.

---

## Parte 3 — Mapeamento consolidado

| Conceito | Arquivo | Função/Classe | Aplicação no Finaxis |
|---|---|---|---|
| Classificação das linguagens | `app.py`, `database.py` | Módulo e funções | Python de alto nível, interpretada, dinâmica e multiparadigma |
| Critérios de avaliação | `database.py`, testes | `conn`, `money`, `DatabaseTests` | Legibilidade, confiabilidade, custo, portabilidade e manutenibilidade |
| Paradigmas | Todos | `notify_error`, `tx_form`, `DatabaseTests` | Procedimental predominante, com elementos funcional e OOP |
| Métodos de implementação | `app.py` | Execução do script Streamlit | Interpretação CPython e reexecução por eventos; sem compilação/JIT própria |
| A linguagem Python | Todos | Módulos, funções e classes | Sintaxe, indentação, imports, docstrings e organização modular |
| Variáveis | Todos | `uid`, `u`, `SESSION_TIMEOUT_MINUTES`, `self.uid` | Locais, globais, constantes e atributos de instância |
| Tipos e expressões | Todos | `money`, `tx_df`, `card_invoice` | `str`, `int`, `float`, `bool`, `None`, listas, tuplas, dicionários, conjuntos, `Decimal`, datas, `bytes` |
| Atribuição, entrada e saída | `app.py`, `database.py` | Widgets, `tx_form`, backup/exportação | Formulários, banco, JSON, CSV, XLSX e PDF |
| Decisão e repetição | Todos | `app.py`, `run_recurring`, `accounts` | `if/elif/else`, `for`, `while`, compreensões e validações |
| Subprogramas | Todos | `money`, `conn`, `notify_error`, `tx_form` | Parâmetros, valores padrão, `**kwargs`, lambdas, geradores e contexto |
| Bibliotecas | Todos | Imports e chamadas | Biblioteca padrão + Streamlit, pandas, Plotly, openpyxl e reportlab |
| Eventos | `app.py` | `st.button`, formulários, `st.rerun` | Modelo orientado a eventos do Streamlit; sem callbacks customizados |
| OOP | `app.py`, `database.py`, testes | `DataFrame`, `Path`, `Decimal`, `DatabaseTests` | Objetos de bibliotecas e classe de testes; sem classes de domínio próprias |
| OOP em Python | `tests/test_database.py` | `DatabaseTests` | Classe, `self`, atributos, métodos, `setUp`/`tearDown` |
| Herança e polimorfismo | `tests/test_database.py` | `DatabaseTests(unittest.TestCase)` | Herança, sobrescrita e métodos herdados; polimorfismo parcial |

---

## Parte 4 — Conceitos não identificados ou identificados apenas parcialmente

### Não identificados

1. **Classes de domínio próprias:** não existem classes como `Usuario`, `Conta`, `Transacao`, `Cartao` ou `Orcamento`. O domínio é representado por dicionários e tabelas.
2. **Polimorfismo por hierarquia própria:** não há subclasses de domínio, classes abstratas, interfaces ou protocolos definidos pelo projeto.
3. **Herança múltipla e MRO:** não são usadas.
4. **Sobrecarga de operadores:** não há implementação de `__add__`, `__eq__`, `__str__` ou similares em classes próprias.
5. **Metaclasses, descritores e decoradores próprios:** apenas decoradores de bibliotecas, como `@contextmanager`.
6. **Compilação, JIT e tipagem estática obrigatória:** o projeto é interpretado e dinamicamente tipado; não há pipeline de compilação ou verificação estática.
7. **Paradigma declarativo ou lógico:** não há Prolog, regras lógicas ou DSL declarativa implementada no projeto. O SQL é declarativo, mas é usado por meio de strings e da biblioteca `sqlite3`.
8. **Programação concorrente/assíncrona:** não foram identificados `async`, `await`, threads ou processos próprios.
9. **Callbacks explícitos de eventos:** não há `on_change`, `on_click` ou `on_select` definidos pelo projeto.
10. **Interface desktop nativa:** a interface é web, construída com Streamlit.

### Identificados apenas parcialmente

1. **Orientação a objetos:** usada por meio de bibliotecas e da classe de testes, mas não como modelagem principal do domínio.
2. **Polimorfismo:** aparece na sobrescrita de `setUp`/`tearDown` e no uso uniforme de métodos de bibliotecas, mas não em uma hierarquia própria.
3. **Eventos:** o modelo do Streamlit é orientado a eventos, mas o projeto usa principalmente o retorno dos widgets após reexecução, não callbacks customizados.
4. **Critérios de avaliação:** são aplicáveis ao projeto, mas não existe um artefato de código específico que os implemente.
5. **Métodos de implementação:** a interpretação é evidente; compilação e JIT não fazem parte do projeto.

---

## Parte 5 — Conclusão e validação

O Finaxis aplica os conceitos dos Temas 2 a 5 de forma coerente com uma aplicação real. Os conceitos mais evidentes são variáveis, tipos, expressões, atribuição, entrada/saída, decisão, repetição, subprogramas, bibliotecas e eventos. A orientação a objetos existe, mas é limitada: aparece no uso de objetos de bibliotecas e na classe `DatabaseTests`, não em uma camada de modelos de domínio.

A análise também permite concluir que o projeto é predominantemente procedimental, com apoio funcional e OOP periférica. Essa conclusão é importante para não superestimar o uso de orientação a objetos apenas porque o projeto utiliza bibliotecas orientadas a objetos.

### Validação executada

- `python -m py_compile app.py database.py tests/test_database.py`: **sucesso**, sem erros de sintaxe.
- `python -m unittest discover -s tests -v`: **28 testes executados, todos aprovados** (`OK`, aproximadamente 11 segundos).
- Comparação de AST entre os arquivos originais (backup) e os arquivos comentados, ignorando docstrings: **AST idêntica nos três arquivos**, confirmando que a lógica foi preservada.
- Nenhuma alteração foi feita em banco de dados, dependências, configuração ou funcionalidades.

### Arquivos modificados

- `app.py`
- `database.py`
- `tests/test_database.py`
- `docs/ANALISE_CONCEITOS_PYTHON_FINAXIS.md` (este documento)

### Resultado

A entrega fica composta por código comentado, docstrings didáticas, relatório de conceitos e validação técnica. Os conceitos ausentes ou parciais foram registrados explicitamente, sem inferências indevidas.
