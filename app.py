"""Interface web do Finaxis, construída com Streamlit.

Mapa didático dos conceitos de Python aplicados neste arquivo:

- Tema 2: escolha de uma linguagem de alto nível, interpretada e dinâmica;
  uso de mais de um paradigma (procedimental, funcional e orientado a objetos
  por meio das bibliotecas).
- Tema 3: variáveis, tipos de dados, expressões, atribuição, entrada e saída.
- Tema 4: decisões, repetições, subprogramas, bibliotecas e eventos.
- Tema 5: objetos fornecidos por bibliotecas e uso de classes de teste no
  arquivo de testes. A interface em si é organizada por funções e por um
  script Streamlit, não por classes de domínio próprias.

Este arquivo é executado de cima para baixo pelo Streamlit. Cada interação do
usuário provoca uma nova execução do script; por isso, o estado precisa ser
mantido em st.session_state.
"""

from __future__ import annotations

# CONCEITO: BIBLIOTECAS E MÓDULOS
# O programa reaproveita módulos da biblioteca padrão (io, os, shutil,
# tempfile, uuid, datetime, decimal, pathlib) e bibliotecas externas
# (pandas, plotly e streamlit). A instrução import disponibiliza funções e
# classes já implementadas, evitando reescrever soluções prontas.
import io, os, shutil, tempfile, uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import database as db

# CONCEITO: EVENTOS E EXECUÇÃO INTERPRETADA
# O Streamlit é um framework orientado a eventos: a página é interpretada a
# cada clique, envio de formulário ou alteração de campo. Não existe um
# laço principal escrito por nós; o próprio framework controla o ciclo de
# eventos e reexecuta este arquivo.
st.set_page_config(page_title="Finaxis", page_icon="💠", layout="wide", initial_sidebar_state="expanded")

# CONCEITO: SUBPROGRAMA
# init_db encapsula a criação e a atualização da estrutura do banco. A
# chamada abaixo é suficiente para preparar a aplicação antes da interface.
db.init_db()

# CONCEITO: VARIÁVEIS, ATRIBUIÇÃO E TIPOS DE DADOS
# theme_css recebe uma string de várias linhas. Ela concentra variáveis CSS
# (--finaxis-*) usadas para padronizar cores e medidas da interface.
# A atribuição cria o nome theme_css e associa a ele o valor à direita.
theme_css = """
<style>
:root {
    --finaxis-bg: #F5F6F8;
    --finaxis-sidebar: #FFFFFF;
    --finaxis-card: #FFFFFF;
    --finaxis-text: #20242B;
    --finaxis-muted: #687385;
    --finaxis-border: #E1E5EA;
    --finaxis-accent: #A78328;
}
.stApp, [data-testid="stAppViewContainer"] {
    background: var(--finaxis-bg) !important;
    color: var(--finaxis-text) !important;
}
.block-container { max-width: 1400px; padding-top: 1.8rem; padding-bottom: 3rem; }
.finaxis-metric-card {
    min-height: 104px; height: 104px; box-sizing: border-box;
    display: flex; flex-direction: column; justify-content: center;
    gap: 8px; padding: 15px 16px; border-radius: 15px;
    background: var(--finaxis-card); border: 1px solid var(--finaxis-border);
    overflow: hidden;
}
.finaxis-metric-label { font-size: 0.92rem; line-height: 1.25; color: var(--finaxis-muted); }
.finaxis-metric-value {
    font-size: clamp(1.35rem, 2vw, 2rem); line-height: 1.15;
    font-weight: 650; letter-spacing: -0.025em; white-space: nowrap;
    color: var(--finaxis-text); font-variant-numeric: tabular-nums;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
    background: var(--finaxis-sidebar) !important;
    border-right: 1px solid var(--finaxis-border) !important;
}
[data-testid="stSidebar"] * { color: var(--finaxis-text); }
[data-testid="stMetric"], [data-testid="stPlotlyChart"],
div[data-testid="stForm"], [data-testid="stExpander"] {
    background: var(--finaxis-card) !important;
    color: var(--finaxis-text) !important;
    border: 1px solid var(--finaxis-border) !important;
    border-radius: 14px !important;
}
h1, h2, h3, h4, p, label { color: var(--finaxis-text); }
[data-testid="stCaptionContainer"], small { color: var(--finaxis-muted); }
[data-testid="stSidebar"] [data-testid="stButton"] button {
    min-height: 42px; border-radius: 9px !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #F4EEDC !important; border-color: #D8C58D !important;
    color: #493A16 !important;
}
button[kind="primary"], [data-testid="stFormSubmitButton"] button {
    border-radius: 9px !important;
}
@media (max-width: 800px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
}
</style>
"""

# CONCEITO: SAÍDA DE DADOS
# st.markdown envia o conteúdo para a página. O parâmetro
# unsafe_allow_html permite que o navegador interprete o bloco de estilo.
st.markdown(theme_css, unsafe_allow_html=True)


# CONCEITO: SUBPROGRAMA E EXPRESSÃO CONDICIONAL
# money é uma função curta que consulta a moeda do usuário e delega a
# formatação para db.fmt. O operador or e o método get evitam erro quando o
# dicionário global u ainda não existe ou não possui a chave "moeda".
def money(v): return db.fmt(v, (globals().get("u") or {}).get("moeda", "BRL"))

def show_dataframe(data, **kwargs):
    """Renderiza tabelas HTML para que o CSS dos temas controle células e cabeçalhos.

    Conceitos aplicados:
    - **kwargs: recebe argumentos nomeados extras sem fixar seus nomes.
    - dict.pop: remove opções específicas antes de repassar o restante.
    - hasattr: verifica dinamicamente se o objeto possui um método.
    - Orientação a objetos: data pode ser um DataFrame do pandas, e o método
      reset_index pertence a esse objeto.
    """
    # CONCEITO: PARÂMETROS VARIÁVEIS (**KWARGS)
    # hide_index é retirado do dicionário kwargs; se não existir, recebe False.
    # As opções theme e width são descartadas para manter compatibilidade com
    # versões diferentes do Streamlit e evitar argumentos não suportados.
    hide_index = kwargs.pop("hide_index", False)
    kwargs.pop("theme", None)
    kwargs.pop("width", None)

    # CONCEITO: ORIENTAÇÃO A OBJETOS E CHAMADA DE MÉTODO
    # reset_index é um método do objeto DataFrame. hasattr evita chamar o
    # método quando o valor recebido não é um DataFrame.
    if hide_index and hasattr(data, "reset_index"):
        data = data.reset_index(drop=True)
    st.table(data)

def notify_error(fn):
    """Executa uma operação e transforma exceções em mensagens para o usuário.

    A função recebe outra função como argumento (função de ordem superior),
    executa-a e trata qualquer exceção com try/except. Isso evita repetir o
    mesmo bloco de tratamento em todos os formulários da interface.
    """
    # CONCEITO: TRATAMENTO DE EXCEÇÕES
    # O bloco try protege a chamada fn(). Se ocorrer erro, o bloco except
    # captura a exceção, mostra a mensagem com st.error e devolve None.
    try:
        result=fn()
        # CONCEITO: EXPRESSÃO CONDICIONAL (OPERADOR TERNÁRIO)
        # Se result for None, devolve True (operação concluída sem valor de
        # retorno); caso contrário, devolve o próprio resultado.
        return True if result is None else result
    except Exception as e:
        st.error(str(e))
        return None

# CONCEITO: DICIONÁRIO, MEMBERSHIP E ESTADO DA SESSÃO
# st.session_state funciona como um dicionário persistente entre reexecuções.
# O operador in verifica se a chave já existe; se não existir, ela é criada
# com o valor None. Esse valor representa "nenhum usuário autenticado".
if "user_id" not in st.session_state: st.session_state.user_id=None

# CONCEITO: CONSTANTE E EXPRESSÃO NUMÉRICA
# O nome em maiúsculas indica uma constante lógica. O valor é usado no
# cálculo de expiração da sessão.
SESSION_TIMEOUT_MINUTES=30

# CONCEITO: DECISÃO E CÁLCULO COM DATAS
# datetime.now() devolve um objeto datetime; a subtração entre dois objetos
# datetime produz um timedelta, e total_seconds() converte a diferença em
# segundos para comparar com o limite de 30 minutos.
if st.session_state.user_id:
    last=st.session_state.get("last_activity")
    if last and (datetime.now()-last).total_seconds()>SESSION_TIMEOUT_MINUTES*60:
        st.session_state.clear()
        st.warning("Sua sessão expirou por inatividade. Entre novamente.")
        st.rerun()
    st.session_state.last_activity=datetime.now()

# CONCEITO: DECISÃO (IF) E ENTRADA/SAÍDA
# Enquanto não há usuário autenticado, a aplicação mostra a tela de login.
# Os widgets st.text_input e st.form_submit_button são as entradas; st.markdown,
# st.write, st.info e st.error são as saídas exibidas ao usuário.
if not st.session_state.user_id:
    # CONCEITO: ATRIBUIÇÃO MÚLTIPLA
    # st.columns devolve uma sequência; a atribuição desempacota os dois
    # elementos nas variáveis left e right.
    left, right=st.columns([1.2,1])
    with left:
        st.markdown("# 💠 Finaxis")
        st.subheader("Sua vida financeira, organizada.")
        st.write("Controle receitas, despesas, contas, cartões, orçamentos e relatórios em um só lugar.")
        st.info("Cada conta possui dados isolados. Senhas são armazenadas com hash seguro.")
    with right:
        login_tab, signup_tab=st.tabs(["Entrar","Criar conta"])
        with login_tab:
            with st.form("login"):
                email=st.text_input("E-mail",key="login_email")
                senha=st.text_input("Senha",type="password",key="login_password")
                ok=st.form_submit_button("Entrar",width="stretch")
            # CONCEITO: EVENTO DE FORMULÁRIO E DECISÃO ANINHADA
            # ok só é verdadeiro quando o botão do formulário é acionado.
            # A partir daí, o código decide se a conta está bloqueada e se as
            # credenciais informadas são válidas.
            if ok:
                if db.login_locked(email): st.error("Muitas tentativas. Aguarde 15 minutos antes de tentar novamente.")
                else:
                    u=db.authenticate(email,senha)
                    if u:
                        db.audit_event(u["id"],"login_sucesso","Autenticação realizada")
                        st.session_state.user_id=u["id"]; st.session_state.last_activity=datetime.now(); st.rerun()
                    else: st.error("E-mail ou senha inválidos.")
        with signup_tab:
            with st.form("signup"):
                nome=st.text_input("Nome")
                email=st.text_input("E-mail",key="signup_email")
                senha=st.text_input("Senha (mínimo 10 caracteres)",type="password",key="signup_password")
                senha2=st.text_input("Confirmar senha",type="password")
                ok=st.form_submit_button("Criar conta",width="stretch")
            if ok:
                # CONCEITO: COMPARAÇÃO, LAMBDA E FUNÇÃO DE ORDEM SUPERIOR
                # A lambda adia a chamada de db.create_user até que
                # notify_error a execute. Assim, exceções de validação são
                # convertidas em mensagens amigáveis.
                if senha!=senha2: st.error("As senhas não coincidem.")
                else:
                    uid=notify_error(lambda: db.create_user(nome,email,senha))
                    if uid:
                        db.audit_event(uid,"conta_criada","Cadastro de usuário")
                        st.session_state.user_id=uid; st.session_state.last_activity=datetime.now(); st.success("Conta criada!"); st.rerun()
    # st.stop interrompe a execução do restante do script nesta reexecução.
    st.stop()

# CONCEITO: VARIÁVEIS E ACESSO A DICIONÁRIO
# uid recebe o identificador guardado na sessão. u recebe um dicionário com
# os dados do usuário. A chave u["nome"] é usada mais adiante na interface.
uid=st.session_state.user_id
u=db.user(uid)
if not u:
    st.session_state.user_id=None; st.rerun()

# CONCEITO: DECISÃO IF/ELSE E SAÍDA COM HTML
# A preferência de tema é consultada no banco. Dependendo do valor, um bloco
# diferente de CSS é enviado para a página. O CSS é apenas apresentação e
# não altera as regras de negócio.
if db.get_theme(uid)=="Escuro":
    st.markdown("""<style>
    :root {
        color-scheme: dark;
        --finaxis-bg:#0D0D0B; --finaxis-sidebar:#171713; --finaxis-card:#202019;
        --finaxis-text:#F2EBDD; --finaxis-muted:#B8B2A3; --finaxis-border:#49432F;
        --finaxis-accent:#D5B45C;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background:#0D0D0B!important; color:#F2EBDD!important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background:#171713!important; border-right:1px solid #49432F!important;
    }
    [data-testid="stSidebar"] * { color:#F2EBDD!important; }
    .finaxis-metric-card {
        background:linear-gradient(145deg,#24231C 0%,#1B1A15 100%)!important;
        border:1px solid #49432F!important;
    }
    .finaxis-metric-label { color:#B8B2A3!important; }
    .finaxis-metric-value { color:#F2EBDD!important; }
    [data-testid="stMetric"], [data-testid="stPlotlyChart"], div[data-testid="stForm"],
    [data-testid="stExpander"], [data-testid="stContainer"] {
        background:#202019!important; color:#F2EBDD!important;
        border-color:#49432F!important;
    }
    h1,h2,h3,h4,h5,p,label,span,legend,
    [data-testid="stMarkdownContainer"], [data-testid="stText"],
    [data-testid="stCaptionContainer"], .stMarkdown, .stText {
        color:#F2EBDD;
    }
    [data-testid="stCaptionContainer"], small, .stCaption {
        color:#B8B2A3!important;
    }

    /* Tabelas nativas e DataFrame */
    [data-testid="stDataFrame"], [data-testid="stTable"],
    [data-testid="stDataFrame"] > div, [data-testid="stTable"] > div {
        background:#202019!important; color:#F2EBDD!important;
        border:1px solid #49432F!important; border-radius:10px!important;
    }
    [data-testid="stDataFrame"] iframe {
        color-scheme:dark!important; background:#202019!important;
    }
    [data-testid="stTable"] table, [data-testid="stTable"] thead,
    [data-testid="stTable"] tbody, [data-testid="stTable"] tr,
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        background:#202019!important; color:#F2EBDD!important;
        border-color:#49432F!important;
    }
    [data-testid="stTable"] th { background:#302B1E!important; color:#F7E7B3!important; }

    /* Botões: texto legível em estados normal, hover, foco e desabilitado */
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button,
    [data-testid="stLinkButton"] a {
        background:#302B1E!important; color:#FFF7E5!important;
        border:1px solid #B99A4A!important; border-radius:9px!important;
        font-weight:600!important; opacity:1!important;
    }
    [data-testid="stButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stLinkButton"] a:hover {
        background:#514321!important; color:#FFFFFF!important;
        border-color:#E0C36F!important;
    }
    [data-testid="stButton"] button:focus,
    [data-testid="stFormSubmitButton"] button:focus,
    [data-testid="stDownloadButton"] button:focus {
        outline:2px solid #E0C36F!important; outline-offset:2px!important;
    }
    [data-testid="stButton"] button:disabled,
    [data-testid="stFormSubmitButton"] button:disabled,
    [data-testid="stDownloadButton"] button:disabled {
        background:#292820!important; color:#B8B2A3!important;
        border-color:#5A523D!important; opacity:1!important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background:transparent!important; color:#F2EBDD!important; border-color:transparent!important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        background:#332D1D!important; border-color:#D5B45C!important; color:#FFFFFF!important;
    }

    /* Campos de entrada, caixas de seleção e menus */
    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"],
    [data-baseweb="select"] > div, [data-testid="stDateInput"] input,
    [data-testid="stNumberInput"] input {
        background:#202019!important; color:#FFF7E5!important;
        border-color:#625638!important; caret-color:#FFFFFF!important;
    }
    input::placeholder, textarea::placeholder { color:#B8B2A3!important; opacity:1!important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"],
    [data-baseweb="select"] ul, [data-baseweb="select"] li {
        background:#202019!important; color:#F2EBDD!important;
    }
    [role="option"], [role="menuitem"] { color:#F2EBDD!important; }
    [role="option"]:hover, [role="option"][aria-selected="true"] {
        background:#40371F!important; color:#FFFFFF!important;
    }

    /* Alertas, mensagens de validação e caixas informativas */
    [data-testid="stAlert"] {
        background:#28251C!important; border:1px solid #65542D!important;
        color:#FFF2D2!important;
    }
    [data-testid="stAlert"] * { color:#FFF2D2!important; }
    [data-testid="stNotification"] { background:#28251C!important; color:#FFF2D2!important; }
    [data-testid="stHeader"] { background:rgba(13,13,11,.98)!important; }
    [data-testid="stToolbar"] { background:transparent!important; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] details {
        color:#F2EBDD!important;
    }
    [data-testid="stTabs"] button { color:#F2EBDD!important; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color:#F3D47B!important; border-bottom-color:#D5B45C!important;
    }
    [data-testid="stProgress"] > div > div { background:#D5B45C!important; }
    </style>""",unsafe_allow_html=True)
else:
    st.markdown("""<style>
    [data-testid="stAlert"]{background:#EEF4FC!important;color:#253247!important;border:1px solid #DCE6F2!important}
    [data-testid="stHeader"]{background:rgba(245,246,248,.96)!important}
    [data-testid="stPlotlyChart"]{background:#FFFFFF!important}
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button {
        color:#20242B!important; opacity:1!important;
    }
    [data-testid="stButton"] button:disabled,
    [data-testid="stFormSubmitButton"] button:disabled,
    [data-testid="stDownloadButton"] button:disabled {
        color:#687385!important; opacity:1!important;
    }
    </style>""",unsafe_allow_html=True)
# CONCEITO: SUBPROGRAMAS E EFEITOS NO BANCO
# run_recurring gera os lançamentos vencidos; notifications devolve uma lista
# de dicionários. As duas chamadas executam regras do módulo database.py.
db.run_recurring(uid)
notifs=db.notifications(uid)

# CONCEITO: CONTEXTO (WITH) E SAÍDA NA BARRA LATERAL
# O bloco with st.sidebar define a região da tela em que os componentes serão
# desenhados. O dicionário u é consultado com u['nome'] e u.get('role').
with st.sidebar:
    st.markdown("## 💠 Finaxis")
    st.caption("Sessão protegida · expira após 30 minutos de inatividade")
    st.caption(f"Olá, {u['nome']}")
    if u.get("role") == "admin":
        st.caption("Perfil: Administrador · Demonstração")

    # CONCEITO: LISTA DE TUPLAS
    # Cada item é uma tupla (nome, ícone). A lista mantém a ordem dos itens
    # exibidos no menu e permite percorrer a navegação com um for.
    paginas = [
        ("Visão geral", ":material/dashboard:"),
        ("Lançamentos", ":material/receipt_long:"),
        ("Nova movimentação", ":material/add_circle:"),
        ("Contas", ":material/account_balance_wallet:"),
        ("Cartões de crédito", ":material/credit_card:"),
        ("Orçamentos", ":material/savings:"),
        ("Recorrências", ":material/repeat:"),
        ("Relatórios", ":material/analytics:"),
        ("Notificações", ":material/notifications:"),
        ("Categorias", ":material/category:"),
        ("Configurações", ":material/settings:")
    ]

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "Visão geral"

    st.caption("NAVEGAÇÃO")

    # CONCEITO: REPETIÇÃO FOR E DESEMPACOTAMENTO DE TUPLA
    # O for percorre a lista; em cada volta, nome e icone recebem os dois
    # valores da tupla. O if interno decide o estilo do botão selecionado.
    for nome, icone in paginas:
        selecionada = st.session_state.pagina_atual == nome

        # CONCEITO: EVENTO DE BOTÃO
        # st.button devolve True apenas na reexecução causada pelo clique.
        # Quando isso acontece, a página atual é trocada e st.rerun solicita
        # uma nova execução com o novo estado.
        if st.button(
            nome,
            key=f"menu_{nome}",
            icon=icone,
            type="primary" if selecionada else "secondary",
            width="stretch"
        ):
            st.session_state.pagina_atual = nome
            st.rerun()

    page = st.session_state.pagina_atual

    st.divider()
    # CONCEITO: EXPRESSÃO GERADORA E SUM
    # O generator soma 1 para cada notificação cujo campo 'lida' seja falso.
    st.caption(
        f"{sum(1 for n in notifs if not n['lida'])} notificação(ões) não lida(s)"
    )

    if st.button("Sair", width="stretch"):
        db.audit_event(uid, "logout", "Encerramento da sessão")
        st.session_state.clear()
        st.rerun()


def tx_df(rows):
    """Converte uma lista de dicionários de lançamentos em um DataFrame.

    Conceitos aplicados:
    - Tipo de dado lista e tipo de dado dicionário.
    - List comprehension para transformar cada registro em uma linha.
    - Expressão condicional para tratar a lista vazia.
    - Objeto DataFrame, da biblioteca pandas, que organiza os dados em
      colunas e linhas para exibição e exportação.
    """
    # CONCEITO: ESTRUTURA DE DECISÃO E LISTA VAZIA
    # Uma lista vazia é considerada False em Python. Nesse caso, devolve-se um
    # DataFrame vazio, porém com as colunas esperadas, evitando erro na tela.
    if not rows: return pd.DataFrame(columns=["ID","Data","Tipo","Descrição","Categoria","Conta","Valor","Status","Observações"])

    # CONCEITO: LIST COMPREHENSION E DICIONÁRIO
    # Para cada r em rows, um novo dicionário é criado. O método title()
    # padroniza a primeira letra do tipo, e r.get("observacoes","") evita
    # KeyError quando a chave não existe.
    return pd.DataFrame([{"ID":r["id"],"Data":r["data"],"Tipo":r["tipo"].title(),"Descrição":r["descricao"],"Categoria":r["categoria"],"Conta":r["conta"],"Valor":float(db.money(r["valor"])),"Status":r["status"] or "Concluído","Observações":r.get("observacoes","")} for r in rows])

def tx_form(prefix, default_tipo="despesa"):
    """Desenha o formulário reutilizável de receita/despesa.

    O prefixo permite que o mesmo formulário seja usado em mais de um lugar
    sem colisão de chaves no estado do Streamlit. O parâmetro default_tipo
    possui valor padrão, um recurso de subprogramas em Python.
    """
    # CONCEITO: ENTRADA DE DADOS COM WIDGETS
    # selectbox, number_input, date_input, text_input e text_area são
    # componentes de entrada. Cada um devolve o valor escolhido pelo usuário.
    tipo=st.selectbox("Tipo",["despesa","receita"],index=0 if default_tipo=="despesa" else 1,key=prefix+"tipo")
    cats=db.categories(uid,tipo); accs=db.accounts(uid)

    # CONCEITO: F-STRING, CHAVE DE DICIONÁRIO E ESTADO
    # A f-string monta o nome da chave. Se a chave ainda não existe no
    # session_state, uuid4().hex gera um identificador único para o envio.
    submission_state_key=f"{prefix}_submission_key"
    if submission_state_key not in st.session_state:
        st.session_state[submission_state_key]=uuid.uuid4().hex

    # CONCEITO: FORMULÁRIO E EVENTO
    # clear_on_submit limpa os campos após o envio. O formulário só dispara
    # a lógica quando o botão submit é acionado.
    with st.form(prefix+"form",clear_on_submit=True):
        descricao=st.text_input("Descrição")
        c1,c2,c3=st.columns(3)
        valor=c1.number_input("Valor (R$)",min_value=0.01,value=10.0,step=1.0,format="%.2f")
        data_l=c2.date_input("Data",value=date.today())
        categoria=c3.selectbox("Categoria",[x["nome"] for x in cats] or ["Outros"])
        conta=st.selectbox("Conta",[x["nome"] for x in accs] or ["Conta principal"])
        status=st.selectbox("Situação",["pendente","pago"]) if tipo=="despesa" else None
        obs=st.text_area("Observações",height=70)
        submit=st.form_submit_button("Salvar lançamento",width="stretch")

    # CONCEITO: EVENTO, LAMBDA E IDEMPOTÊNCIA
    # A lambda encapsula a chamada do banco. A mesma chave é enviada para
    # add_transaction; se o navegador repetir o envio, o banco reconhece a
    # chave e não cria um segundo lançamento.
    if submit:
        request_key=st.session_state[submission_state_key]
        result=notify_error(lambda: db.add_transaction(
            uid,tipo,descricao,valor,data_l.isoformat(),categoria,conta,status,obs,
            submission_key=request_key
        ))
        if result:
            st.session_state[submission_state_key]=uuid.uuid4().hex
            st.success("Lançamento salvo com sucesso.")
            st.rerun()

# CONCEITO: DECISÃO IF/ELIF
# A variável page guarda a página escolhida. A cadeia if/elif seleciona
# apenas um bloco de interface por reexecução. O mesmo padrão se repete nas
# demais páginas do sistema.
if page=="Visão geral":
    st.title("Visão geral")
    st.caption("Seu resumo financeiro e os próximos compromissos.")

    # CONCEITO: DATAS, STRINGS E CHAMADA DE SUBPROGRAMA
    # strftime formata a data como AAAA-MM; replace(day=1) obtém o primeiro
    # dia do mês; isoformat devolve uma string adequada ao banco. db.summary
    # encapsula o cálculo dos totais.
    mes=date.today().strftime("%Y-%m")
    ini=date.today().replace(day=1).isoformat()
    resumo=db.summary(uid,ini,date.today().isoformat())
    # Monthly totals include all month's transactions, not just up to today.
    import calendar
    month_end=date.today().replace(day=calendar.monthrange(date.today().year,date.today().month)[1])
    allmonth=db.list_transactions(uid,{"inicio":ini,"fim":month_end.isoformat()})

    # CONCEITO: EXPRESSÕES GERADORAS, SUM E DECIMAIS
    # Cada sum percorre allmonth, filtra pelo tipo/status e soma valores
    # convertidos para Decimal. O segundo argumento de sum define o valor
    # inicial zero, evitando somar float com Decimal.
    receitas=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="receita"),db.money(0))
    pagas=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="despesa" and x["status"]=="pago"),db.money(0))
    pend=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="despesa" and x["status"]=="pendente"),db.money(0))

    # CONCEITO: LISTA DE TUPLAS E FOR COM ZIP
    # metric_items associa rótulo e valor. zip combina cada coluna com o
    # respectivo par, permitindo desempacotar (label, value) no for.
    metric_cols=st.columns(4, gap="medium")
    metric_items=[
        ("Receitas do mês",money(receitas)),
        ("Despesas pagas",money(pagas)),
        ("Despesas pendentes",money(pend)),
        ("Saldo do período",money(receitas-pagas)),
    ]
    for col,(label,value) in zip(metric_cols,metric_items):
        with col:
            # CONCEITO: F-STRING E SAÍDA HTML
            # As chaves {label} e {value} interpolam os valores na string.
            st.markdown(
                f'<div class="finaxis-metric-card"><div class="finaxis-metric-label">{label}</div>'
                f'<div class="finaxis-metric-value">{value}</div></div>',
                unsafe_allow_html=True
            )

    # CONCEITO: ARITMÉTICA DE DATAS COM TIMEDELTA
    # Subtrair um dia do primeiro dia do mês atual obtém o último dia do mês
    # anterior. Depois, replace(day=1) encontra o primeiro dia desse mês.
    import calendar
    first_day=date.today().replace(day=1)
    prev_first=first_day-timedelta(days=1)
    prev_start=prev_first.replace(day=1).isoformat()
    prev_rows=db.list_transactions(uid,{"inicio":prev_start,"fim":prev_first.isoformat()})
    prev_rec=sum(float(x["valor"]) for x in prev_rows if x["tipo"]=="receita")
    prev_desp=sum(float(x["valor"]) for x in prev_rows if x["tipo"]=="despesa" and x["status"]=="pago")
    st.caption(f"Mês anterior: receitas {money(prev_rec)} · despesas pagas {money(prev_desp)}")
    rows=db.list_transactions(uid,{"inicio":ini,"fim":date.today().isoformat()})
   
    
    # CONCEITO: BIBLIOTECAS
    # go é um apelido para plotly.graph_objects, importado apenas nesta parte
    # do código. Isso mostra que bibliotecas podem ser importadas no escopo
    # local, quando são necessárias.
    import math
    import plotly.graph_objects as go

    a, b = st.columns(2, gap="large")

    # ===== DESPESAS POR CATEGORIA — AUREN SUN =====
    with a:
        st.subheader("Despesas por categoria")

        # CONCEITO: LIST COMPREHENSION E DATAFRAME
        # A lista interna cria um dicionário para cada despesa. O DataFrame
        # transforma esses dicionários em uma tabela com as colunas Categoria
        # e Valor, facilitando agrupamento e gráfico.
        df = pd.DataFrame([
            {
                "Categoria": x["categoria"],
                "Valor": float(x["valor"])
            }
            for x in rows if x["tipo"] == "despesa"
        ])

        if not df.empty:
            # CONCEITO: MÉTODOS ENCADEADOS E ORIENTAÇÃO A OBJETOS
            # groupby, sum e sort_values são métodos do DataFrame. Cada um
            # devolve um novo objeto, permitindo encadear as operações.
            df = (
                df.groupby("Categoria", as_index=False)["Valor"]
                .sum()
                .sort_values("Valor", ascending=False)
            )

            total_despesas = df["Valor"].sum()

            # Paleta de ouro em tons graduais
            cores_auren = [
                "#A9822F",
                "#BC9740",
                "#CBA84F",
                "#D8B966",
                "#E3C985",
                "#B69A58",
                "#92763C",
                "#D0B477"
            ]

            # CONCEITO: OBJETO E MÉTODO
            # go.Figure() cria um objeto de figura. Os métodos add_trace,
            # update_layout e a chamada st.plotly_chart manipulam esse objeto
            # sem que precisemos conhecer sua estrutura interna.
            fig = go.Figure()

            # Aro externo concêntrico: geometria circular nativa do Plotly.
            aro_cores = ["#8F702B" if i % 6 else "#D8BC70" for i in range(120)]
            fig.add_trace(
                go.Pie(
                    values=[1] * 120,
                    labels=[""] * 120,
                    hole=0.945,
                    sort=False,
                    direction="clockwise",
                    rotation=270,
                    textinfo="none",
                    hoverinfo="skip",
                    showlegend=False,
                    marker=dict(colors=aro_cores, line=dict(color="#242117", width=0.6)),
                    domain=dict(x=[0.04, 0.96], y=[0.05, 0.97])
                )
            )

            fig.add_trace(
                go.Pie(
                    labels=df["Categoria"],
                    values=df["Valor"],
                    hole=0.64,
                    sort=False,
                    direction="clockwise",
                    rotation=270,
                    marker=dict(
                        colors=cores_auren,
                        line=dict(
                            color="#242117",
                            width=1
                        )
                    ),
                    textinfo="percent",
                    textposition="inside",
                    textfont=dict(
                         color="#F2EBDD",
                         size=11
                    ),
                    domain=dict(
                        x=[0.12, 0.88],
                        y=[0.08, 0.94]
                    )
                )
            )

            # O aro externo concêntrico substitui os raios manuais,
            # que ficavam desalinhados em telas com proporções diferentes.

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(
                    l=20,
                    r=20,
                    t=10,
                    b=48
                ),
                font=dict(
                    family="Inter, sans-serif",
                    color="#F2EBDD",
                    size=11
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.06,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        family="Inter, sans-serif",
                        size=10,
                        color="#D8BC70"
                    )
                ),
                annotations=[
                    dict(
                        x=0.5,
                        y=0.51,
                        xref="paper",
                        yref="paper",
                        text=(
                            f"<b>{money(total_despesas)}</b>"
                            "<br><span style='font-size:10px;color:#A9A493'>TOTAL GASTO</span>"
                        ),
                        showarrow=False,
                        font=dict(
                            family="Inter, sans-serif",
                            size=15,
                            color="#F2EBDD"
                        )
                    )
                ]
            )

            st.plotly_chart(fig, width="stretch")

        else:
            st.info("Ainda não há despesas neste período.")

    # ===== EVOLUÇÃO MENSAL — AUREN =====
    with b:
        st.subheader("Evolução mensal")

        alltx = db.list_transactions(uid)

        if alltx:
            # CONCEITO: SLICING DE STRING E LIST COMPREHENSION
            # x["data"][:7] recorta os sete primeiros caracteres (AAAA-MM).
            # A compreensão filtra receitas/despesas e monta as linhas.
            df_evolucao = pd.DataFrame([
                {
                    "Mês": x["data"][:7],
                    "Tipo": x["tipo"].title(),
                    "Valor": float(x["valor"])
                }
                for x in alltx
                if x["tipo"] in ("receita", "despesa")
            ])

            if not df_evolucao.empty:
                agg = (
                    df_evolucao
                    .groupby(
                        ["Mês", "Tipo"],
                        as_index=False
                    )["Valor"]
                    .sum()
                    .sort_values("Mês")
                )

                # CONCEITO: BIBLIOTECA PLOTLY EXPRESS
                # px.bar cria o gráfico a partir do DataFrame. As opções
                # color, barmode e category_orders controlam a apresentação.
                fig = px.bar(
                    agg,
                    x="Mês",
                    y="Valor",
                    color="Tipo",
                    barmode="group",
                    category_orders={
                        "Tipo": ["Receita", "Despesa"]
                    },
                    color_discrete_map={
                        "Receita": "#D8BC70",
                        "Despesa": "#A9822F"
                    }
                )

                fig.update_traces(
                    marker_line=dict(
                        color="rgba(216,188,112,0.35)",
                        width=0.7
                    ),
                    opacity=0.96,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "%{fullData.name}: R$ %{y:,.2f}"
                        "<extra></extra>"
                    )
                )

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=310,
                    margin=dict(
                        l=15,
                        r=15,
                        t=30,
                        b=40
                    ),
                    font=dict(
                        family="Inter, sans-serif",
                        color="#F2EBDD",
                        size=10
                    ),
                    bargap=0.55,
                    bargroupgap=0.12,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="left",
                        x=0,
                        title_text="",
                        font=dict(
                            size=10,
                            color="#D8BC70"
                        )
                    ),
                    xaxis=dict(
                        title="",
                        type="category",
                        showgrid=False,
                        tickfont=dict(color="#A9A493"),
                        linecolor="#39372B"
                    ),
                    yaxis=dict(
                        title="",
                        showgrid=True,
                        gridcolor="rgba(198,164,66,0.10)",
                        zeroline=False,
                        tickprefix="R$ ",
                        tickformat=",.0f",
                        tickfont=dict(color="#A9A493")
                    )
                )

                st.plotly_chart(fig, width="stretch")

            else:
                st.info("Não há lançamentos para exibir.")

        else:
            st.info(
                "Cadastre seu primeiro lançamento "
                "para visualizar a evolução."
            )
    st.subheader("Últimos lançamentos")
    show_dataframe(tx_df(db.list_transactions(uid)[:8]),width="stretch",hide_index=True)
    st.subheader("Orçamentos do mês")
    for bgt in db.budgets(uid,mes):
        lim=bgt["limite_valor"]; spent=bgt["gasto"]
        st.write(f'{bgt["categoria"]}: {money(spent)} / {money(lim)}')
        st.progress(min(1.0,float(spent/lim)) if lim else 0.0)

elif page=="Lançamentos":
    st.title("Lançamentos")
    # CONCEITO: DICIONÁRIO DE FILTROS E ENTRADA DE DADOS
    # Os widgets devolvem valores que são reunidos no dicionário filtros.
    # Esse dicionário é repassado para db.list_transactions, que monta a
    # consulta SQL parametrizada.
    with st.expander("Filtros",expanded=True):
        c1,c2,c3=st.columns(3)
        tipo=c1.selectbox("Tipo",["Todos","receita","despesa","transferencia"])
        catnames=["Todos"]+[x["nome"] for x in db.categories(uid)]
        cat=c2.selectbox("Categoria",catnames)
        acnames=["Todos"]+[x["nome"] for x in db.accounts(uid)]
        conta=c3.selectbox("Conta",acnames)
        c4,c5,c6=st.columns(3)
        inicio=c4.date_input("De",value=date.today().replace(day=1))
        fim=c5.date_input("Até",value=date.today())
        busca=c6.text_input("Buscar descrição")
    filtros={"tipo":tipo,"categoria":cat,"conta":conta,"inicio":inicio.isoformat(),"fim":fim.isoformat(),"busca":busca}
    rows=db.list_transactions(uid,filtros)
    show_dataframe(tx_df(rows),width="stretch",hide_index=True)
    if rows:
        opts={f'#{r["id"]} · {r["data"]} · {r["descricao"]} · {money(r["valor"])}':r for r in rows}
        sel=st.selectbox("Selecionar lançamento para editar ou excluir",list(opts))
        r=opts[sel]
        with st.expander("Editar lançamento"):
            with st.form("edit_tx"):
                desc=st.text_input("Descrição",r["descricao"])
                c1,c2,c3=st.columns(3)
                val=c1.number_input("Valor",min_value=0.01,value=float(db.money(r["valor"])),step=1.0)
                dt=c2.date_input("Data",value=date.fromisoformat(r["data"]))
                cats=[x["nome"] for x in db.categories(uid,r["tipo"])] if r["tipo"] in db.TIPOS else [r["categoria"]]
                catx=c3.selectbox("Categoria",cats,index=cats.index(r["categoria"]) if r["categoria"] in cats else 0)
                accs=[x["nome"] for x in db.accounts(uid)]
                acc=st.selectbox("Conta",accs,index=accs.index(r["conta"]) if r["conta"] in accs else 0)
                status=st.selectbox("Situação",["pendente","pago"],index=0 if r["status"]=="pendente" else 1) if r["tipo"]=="despesa" else None
                obs=st.text_area("Observações",r["observacoes"] or "")
                save=st.form_submit_button("Salvar alterações")
            if save:
                result=notify_error(lambda: db.edit_transaction(uid,r["id"],desc,val,dt.isoformat(),catx,acc,status,obs))
                if result is not None: st.success("Lançamento atualizado."); st.rerun()
        if st.button("Excluir lançamento selecionado",type="secondary"):
            result=notify_error(lambda: db.delete_transaction(uid,r["id"]))
            if result is not None: st.success("Lançamento excluído."); st.rerun()

elif page=="Nova movimentação":
    st.title("Nova movimentação")
    # CONCEITO: ABAS, FORMULÁRIOS E DECISÃO
    # As abas organizam duas operações. Cada formulário só executa sua ação
    # quando o respectivo botão é clicado; a transferência ainda valida se
    # origem e destino são diferentes.
    tab1,tab2=st.tabs(["Receita ou despesa","Transferência entre contas"])
    with tab1:
        tx_form("newtx")
    with tab2:
        accs=db.accounts(uid)
        names=[x["nome"] for x in accs]
        if len(names)<2: st.info("Cadastre pelo menos duas contas para transferir valores.")
        else:
            with st.form("transfer"):
                desc=st.text_input("Descrição",value="Transferência entre contas")
                c1,c2=st.columns(2); origem=c1.selectbox("Conta de origem",names); destino=c2.selectbox("Conta de destino",names,index=1)
                valor=st.number_input("Valor (R$)",min_value=.01,value=10.0)
                dt=st.date_input("Data",value=date.today())
                go=st.form_submit_button("Registrar transferência")
            if go:
                if origem==destino: st.error("Origem e destino devem ser diferentes.")
                else:
                    result=notify_error(lambda: db.add_transfer(uid,desc,valor,dt.isoformat(),origem,destino))
                    if result: st.success("Transferência registrada integralmente."); st.rerun()

elif page=="Contas":
    st.title("Contas")
    # CONCEITO: FORMULÁRIO, VALIDAÇÃO E EXIBIÇÃO TABULAR
    # O formulário coleta nome, tipo e saldo; db.add_account valida e grava.
    # A lista de dicionários é convertida em DataFrame para exibição.
    with st.form("new_account"):
        nome=st.text_input("Nome da conta")
        tipo=st.selectbox("Tipo",["Conta corrente","Poupança","Carteira","Conta digital","Investimento","Outro"])
        saldo=st.number_input("Saldo inicial (R$)",value=0.0,step=50.0)
        go=st.form_submit_button("Adicionar conta")
    if go:
        result=notify_error(lambda: db.add_account(uid,nome,tipo,saldo))
        if result is not None: st.success("Conta adicionada."); st.rerun()
    accs=db.accounts(uid)
    show_dataframe(pd.DataFrame([{"Conta":a["nome"],"Tipo":a["tipo"],"Saldo atual":float(a["saldo"])} for a in accs]),width="stretch",hide_index=True)
    st.caption("O saldo considera receitas e despesas pagas. Transferências entre contas são exibidas no histórico; confira o saldo por conta.")

elif page=="Cartões de crédito":
    st.title("Cartões de crédito")
    # CONCEITO: LISTA, DICIONÁRIO E ACÚMULO
    # O código percorre cartões, consulta o saldo em aberto de cada um e
    # acumula dicionários em card_rows para montar a tabela final.
    tab1,tab2=st.tabs(["Cadastrar cartão","Compras e faturas"])
    with tab1:
        with st.form("card"):
            nome=st.text_input("Nome do cartão")
            limite=st.number_input("Limite (R$)",min_value=0.01,value=1000.0,step=100.0)
            c1,c2=st.columns(2); fechamento=c1.number_input("Dia de fechamento",1,28,20); vencimento=c2.number_input("Dia de vencimento",1,28,5)
            go=st.form_submit_button("Salvar cartão")
        if go:
            result=notify_error(lambda: db.add_card(uid,nome,limite,fechamento,vencimento))
            if result is not None: st.success("Cartão salvo."); st.rerun()
        card_rows=[]
        for x in db.cards(uid):
            outstanding=db.card_outstanding(uid,x["id"])
            limit_value=db.money(x["limite"])
            card_rows.append({"Cartão":x["nome"],"Limite cadastrado":float(limit_value),
                "Faturas atuais e futuras em aberto":float(outstanding),
                "Limite disponível estimado":float(max(db.money(0),limit_value-outstanding)),
                "Fechamento":x["fechamento"],"Vencimento":x["vencimento"]})
        show_dataframe(pd.DataFrame(card_rows),width="stretch",hide_index=True)
        st.caption("O limite disponível é uma estimativa baseada nas parcelas atuais e futuras registradas; compras feitas fora do sistema não são consideradas.")
    with tab2:
        cards=db.cards(uid); cats=db.categories(uid,"despesa")
        if not cards: st.info("Cadastre um cartão primeiro.")
        else:
            with st.form("purchase"):
                cardmap={x["nome"]:x for x in cards}; cardname=st.selectbox("Cartão",list(cardmap))
                desc=st.text_input("Descrição da compra"); val=st.number_input("Valor total (R$)",min_value=.01,value=100.0)
                dt=st.date_input("Data da compra",value=date.today()); cat=st.selectbox("Categoria",[x["nome"] for x in cats])
                parts=st.number_input("Parcelas",1,60,1); go=st.form_submit_button("Registrar compra")
            if go:
                result=notify_error(lambda: db.add_purchase(uid,cardmap[cardname]["id"],desc,val,dt.isoformat(),cat,parts))
                if result is not None: st.success("Compra registrada."); st.rerun()
        ps=db.purchases(uid)
        if ps:
            show_dataframe(pd.DataFrame([{"Data":x["data"],"Cartão":x["cartao"],"Descrição":x["descricao"],"Categoria":x["categoria"],"Total":float(x["valor_total"]),"Parcelas":x["parcelas"],"Valor médio da parcela":float(db.money(x["valor_total"])/x["parcelas"])} for x in ps]),width="stretch",hide_index=True)
        if cards:
            st.divider(); st.subheader("Consultar e pagar fatura")
            cardmap={x["nome"]:x for x in cards}
            fc1,fc2=st.columns(2)
            invoice_card_name=fc1.selectbox("Cartão da fatura",list(cardmap),key="invoice_card")
            invoice_month=fc2.date_input("Mês de fechamento",value=date.today().replace(day=1),key="invoice_month").strftime("%Y-%m")
            invoice=notify_error(lambda: db.card_invoice(uid,cardmap[invoice_card_name]["id"],invoice_month))
            if invoice:
                k1,k2,k3=st.columns(3)
                k1.metric("Total da fatura",money(invoice["total"]))
                k2.metric("Já pago",money(invoice["pago"]))
                k3.metric("Em aberto",money(invoice["aberto"]))
                st.caption(f"Vencimento: {date.fromisoformat(invoice['vencimento']):%d/%m/%Y}")
                if invoice["itens"]:
                    show_dataframe(pd.DataFrame([{"Compra":x["descricao"],"Data":x["data_compra"],"Parcela":f"{x['parcela']}/{x['parcelas']}", "Categoria":x["categoria"],"Valor":float(x["valor"])} for x in invoice["itens"]]),width="stretch",hide_index=True)
                else: st.info("Não há compras nessa fatura.")
                if invoice["aberto"]>0:
                    account_names=[a["nome"] for a in db.accounts(uid)]
                    with st.form("pay_invoice_form"):
                        payment_account=st.selectbox("Pagar usando a conta",account_names)
                        payment_value=st.number_input("Valor do pagamento (R$)",min_value=.01,max_value=float(invoice["aberto"]),value=float(invoice["aberto"]),step=1.0)
                        payment_date=st.date_input("Data do pagamento",value=date.today())
                        payment_obs=st.text_input("Observações do pagamento")
                        pay_go=st.form_submit_button("Registrar pagamento da fatura")
                    if pay_go:
                        paid_result=notify_error(lambda: db.pay_card_invoice(uid,cardmap[invoice_card_name]["id"],invoice_month,payment_value,payment_account,payment_date.isoformat(),payment_obs))
                        if paid_result is not None: st.success("Pagamento registrado e saída lançada na conta selecionada."); st.rerun()
        st.caption("As compras são contabilizadas na fatura. A despesa no fluxo da conta é registrada quando a fatura é paga, evitando duplicação de despesa.")

elif page=="Orçamentos":
    st.title("Orçamentos por categoria")
    # CONCEITO: COMPARAÇÃO COM DECIMAL E DECISÃO
    # Os limites e gastos são Decimal. O código usa > e >= para decidir se
    # mostra erro de limite ultrapassado ou aviso de 80% utilizado.
    mes=st.date_input("Mês de referência",value=date.today().replace(day=1)).strftime("%Y-%m")
    cats=db.categories(uid,"despesa")
    with st.form("budget"):
        cat=st.selectbox("Categoria", [x["nome"] for x in cats] or ["Outros"])
        limite=st.number_input("Limite mensal (R$)",min_value=.01,value=500.0,step=50.0)
        go=st.form_submit_button("Salvar orçamento")
    if go:
        result=notify_error(lambda: db.add_budget(uid,cat,mes,limite))
        if result is not None: st.success("Orçamento salvo."); st.rerun()
    for b in db.budgets(uid,mes):
        spent=b["gasto"]; lim=b["limite_valor"]
        st.write(f'**{b["categoria"]}** — {money(spent)} de {money(lim)}')
        st.progress(min(1.0,float(spent/lim)) if lim else 0.0)
        if spent>lim: st.error("Limite ultrapassado.")
        elif spent >= lim * Decimal("0.8"): st.warning("Atenção: você já utilizou 80% ou mais do orçamento.")

elif page=="Recorrências":
    st.title("Lançamentos recorrentes")
    # CONCEITO: ATRIBUIÇÃO MÚLTIPLA E SELEÇÃO DE LISTA
    # Três chamadas são atribuídas na mesma linha. catsR e catsD guardam
    # listas diferentes; o tipo escolhido decide qual delas será usada.
    accs=db.accounts(uid); catsR=db.categories(uid,"receita"); catsD=db.categories(uid,"despesa")
    with st.form("recurring"):
        tipo=st.selectbox("Tipo",["despesa","receita"])
        descricao=st.text_input("Descrição")
        valor=st.number_input("Valor (R$)",min_value=.01,value=100.0)
        cats=catsD if tipo=="despesa" else catsR
        cat=st.selectbox("Categoria",[x["nome"] for x in cats] or ["Outros"])
        conta=st.selectbox("Conta",[x["nome"] for x in accs] or ["Conta principal"])
        freq=st.selectbox("Frequência",["Diária","Semanal","Mensal","Anual"])
        nxt=st.date_input("Próxima data",value=date.today())
        obs=st.text_input("Observações")
        go=st.form_submit_button("Criar recorrência")
    if go:
        result=notify_error(lambda: db.add_recurring(uid,tipo,descricao,valor,cat,conta,freq,nxt.isoformat(),obs))
        if result is not None: st.success("Recorrência criada."); st.rerun()
    rs=db.recurrings(uid)
    if rs: show_dataframe(pd.DataFrame([{"Descrição":r["descricao"],"Tipo":r["tipo"],"Valor":float(r["valor"]),"Frequência":r["frequencia"],"Próxima data":r["proxima_data"],"Ativa":"Sim" if r["ativo"] else "Não"} for r in rs]),width="stretch",hide_index=True)
    st.caption("As recorrências vencidas são processadas ao abrir a aplicação. Revise os lançamentos gerados no histórico.")

elif page=="Relatórios":
    st.title("Relatórios e exportação")
    # CONCEITO: FILTROS COMBINADOS E VALIDAÇÃO DE DATAS
    # Os filtros são reunidos em um dicionário. A comparação inicio>fim
    # impede consultas com intervalo inválido antes de chamar o banco.
    with st.expander("Filtros do relatório", expanded=True):
        c1,c2,c3=st.columns(3)
        inicio=c1.date_input("Data inicial",value=date.today().replace(day=1),key="rel_inicio")
        fim=c2.date_input("Data final",value=date.today(),key="rel_fim")
        tipo_rel=c3.selectbox("Tipo",["Todos","receita","despesa","transferencia"],key="rel_tipo")
        c4,c5,c6=st.columns(3)
        cat_rel=c4.selectbox("Categoria",["Todos"]+[x["nome"] for x in db.categories(uid)],key="rel_categoria")
        conta_rel=c5.selectbox("Conta",["Todos"]+[x["nome"] for x in db.accounts(uid)],key="rel_conta")
        status_rel=c6.selectbox("Situação",["Todos","pendente","pago","Concluído"],key="rel_status")
        busca_rel=st.text_input("Buscar na descrição ou observações",placeholder="Digite um termo...",key="rel_busca").strip()
    if inicio>fim:
        st.error("A data inicial não pode ser posterior à data final.")
        st.stop()
    filtros={"inicio":inicio.isoformat(),"fim":fim.isoformat(),"tipo":tipo_rel,
             "categoria":cat_rel,"conta":conta_rel,"status":status_rel,"busca":busca_rel}
    rows=db.list_transactions(uid,filtros)
    df=tx_df(rows)
    st.caption(f"{len(rows)} lançamento(s) encontrado(s) com os filtros selecionados.")
    show_dataframe(df,width="stretch",hide_index=True)
    total_rec=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="receita"),db.money(0))
    total_desp=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="despesa" and x.get("status")=="pago"),db.money(0))
    pendentes=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="despesa" and x.get("status")=="pendente"),db.money(0))
    a,b,c,d=st.columns(4)
    a.metric("Receitas",money(total_rec)); b.metric("Despesas pagas",money(total_desp))
    c.metric("Despesas pendentes",money(pendentes)); d.metric("Resultado realizado",money(total_rec-total_desp))

    # CONCEITO: MÉTODO DE OBJETO, CODIFICAÇÃO E SAÍDA DE ARQUIVO
    # to_csv é um método do DataFrame. encode transforma o texto em bytes,
    # formato exigido pelo botão de download. O prefixo utf-8-sig ajuda o
    # Excel a reconhecer corretamente os acentos.
    # Todos os formatos recebem exatamente o mesmo conjunto filtrado.
    csv_bytes=df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Exportar CSV",csv_bytes,"relatorio_finaxis.csv","text/csv",disabled=df.empty)

    # CONCEITO: OBJETO EM MEMÓRIA E CONTEXTO
    # io.BytesIO funciona como um arquivo em memória. O bloco with garante
    # que o escritor do Excel seja finalizado corretamente ao sair do bloco.
    excel=io.BytesIO()
    resumo_df=pd.DataFrame([
        {"Indicador":"Receitas","Valor":float(total_rec)},
        {"Indicador":"Despesas pagas","Valor":float(total_desp)},
        {"Indicador":"Despesas pendentes","Valor":float(pendentes)},
        {"Indicador":"Resultado realizado","Valor":float(total_rec-total_desp)},
        {"Indicador":"Quantidade de lançamentos","Valor":len(rows)},
        {"Indicador":"Período","Valor":f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"},
        {"Indicador":"Filtros","Valor":f"Tipo: {tipo_rel}; Categoria: {cat_rel}; Conta: {conta_rel}; Situação: {status_rel}; Busca: {busca_rel or '—'}"},
    ])
    categorias_df=(df.groupby("Categoria",dropna=False)["Valor"].sum().reset_index()
                   if not df.empty else pd.DataFrame(columns=["Categoria","Valor"]))
    with pd.ExcelWriter(excel,engine="openpyxl") as writer:
        resumo_df.to_excel(writer,index=False,sheet_name="Resumo")
        df.to_excel(writer,index=False,sheet_name="Lançamentos")
        categorias_df.to_excel(writer,index=False,sheet_name="Por categoria")
        for ws in writer.book.worksheets:
            ws.freeze_panes="A2"
            ws.auto_filter.ref=ws.dimensions
            for column_cells in ws.columns:
                letter=column_cells[0].column_letter
                width=min(max(max(len(str(cell.value or "")) for cell in column_cells)+2,12),48)
                ws.column_dimensions[letter].width=width
            for cell in ws[1]:
                cell.font=__import__("openpyxl").styles.Font(bold=True,color="FFFFFF")
                cell.fill=__import__("openpyxl").styles.PatternFill("solid",fgColor="243447")
    st.download_button("Exportar Excel (XLSX)",excel.getvalue(),"relatorio_finaxis.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",disabled=df.empty)

    # CONCEITO: IMPORTAÇÃO LOCAL, TRATAMENTO DE EXCEÇÕES E BIBLIOTECAS
    # As importações de reportlab ficam dentro do try porque essa biblioteca
    # pode não estar instalada. Se ocorrer erro, o except mostra um aviso e
    # o restante da aplicação continua funcionando.
    try:
        from xml.sax.saxutils import escape
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        pdf=io.BytesIO()
        doc=SimpleDocTemplate(pdf,pagesize=landscape(A4),rightMargin=24,leftMargin=24,topMargin=28,bottomMargin=28)
        styles=getSampleStyleSheet()
        cell_style=ParagraphStyle("Cell",parent=styles["BodyText"],fontName="Helvetica",fontSize=7,leading=9,wordWrap="CJK")
        head_style=ParagraphStyle("Head",parent=cell_style,textColor=colors.white,fontName="Helvetica-Bold")
        data=[[Paragraph(x,head_style) for x in ["ID","Data","Tipo","Descrição","Categoria","Conta","Valor","Status"]]]
        for x in rows:
            data.append([
                str(x["id"]),str(x["data"]),str(x["tipo"]).title(),
                Paragraph(escape(str(x["descricao"] or "")),cell_style),
                Paragraph(escape(str(x["categoria"] or "")),cell_style),
                Paragraph(escape(str(x["conta"] or "")),cell_style),
                money(x["valor"]),str(x.get("status") or "Concluído")
            ])
        story=[
            Paragraph("Finaxis — Relatório financeiro",styles["Title"]),
            Paragraph(f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}",styles["Normal"]),
            Paragraph(f"Filtros: Tipo {escape(tipo_rel)} | Categoria {escape(cat_rel)} | Conta {escape(conta_rel)} | Situação {escape(status_rel)} | Busca {escape(busca_rel or '—')}",styles["Normal"]),
            Spacer(1,10),
            Paragraph(f"Receitas: {money(total_rec)} &nbsp;&nbsp; Despesas pagas: {money(total_desp)} &nbsp;&nbsp; Pendentes: {money(pendentes)} &nbsp;&nbsp; Resultado: {money(total_rec-total_desp)}",styles["Normal"]),
            Spacer(1,10)
        ]
        if rows:
            table=Table(data,colWidths=[28,55,58,150,90,90,70,58],repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#243447")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D5DCE5")),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6F9")]),
                ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)
            ]))
            story.append(table)
        else:
            story.append(Paragraph("Nenhum lançamento encontrado para os filtros selecionados.",styles["Normal"]))
        doc.build(story)
        st.download_button("Exportar PDF",pdf.getvalue(),"relatorio_finaxis.pdf","application/pdf",disabled=df.empty)
    except Exception as e:
        st.warning(f"PDF indisponível neste ambiente: {e}")

elif page=="Notificações":
    st.title("Central de notificações")
    # CONCEITO: LISTA, EXPRESSÃO GERADORA E DECISÃO
    # A lista notifs é percorrida para contar as não lidas e para desenhar
    # cada cartão. O botão só aparece quando há notificações pendentes.
    notifs=db.notifications(uid)
    unread=sum(1 for n in notifs if not n["lida"])
    st.caption(f"{unread} notificação(ões) não lida(s) de {len(notifs)} no total.")
    if unread and st.button("Marcar todas como lidas"):
        db.mark_all_notifications_read(uid); st.rerun()
    if not notifs: st.success("Você não tem notificações.")
    for n in notifs:
        with st.container(border=True):
            st.markdown(("🔵 " if not n["lida"] else "⚪ ")+f"**{n['titulo']}**")
            st.write(n["mensagem"]); st.caption(n["criada_em"])
            if not n["lida"] and st.button("Marcar como lida",key=f"read{n['id']}"):
                db.mark_notification_read(uid,n["id"]); st.rerun()

elif page=="Categorias":
    st.title("Categorias")
    # CONCEITO: DICIONÁRIO, SELEÇÃO E FORMULÁRIO
    # cmap associa o texto exibido ao dicionário da categoria. O operador
    # ** combina o item "selecione" com as opções vindas do banco.
    with st.form("newcat"):
        nome=st.text_input("Nome da categoria")
        tipo=st.selectbox("Tipo",["despesa","receita"])
        go=st.form_submit_button("Adicionar categoria")
    if go:
        result=notify_error(lambda: db.add_category(uid,nome,tipo))
        if result is not None: st.success("Categoria adicionada."); st.rerun()
    cats=db.categories(uid)
    show_dataframe(pd.DataFrame([{"ID":x["id"],"Nome":x["nome"],"Tipo":x["tipo"],"Ativa":bool(x["ativo"])} for x in cats]),width="stretch",hide_index=True)
    if cats:
        cmap={f'{x["nome"]} ({x["tipo"]})':x for x in cats}
        chosen=st.selectbox("Selecionar categoria para editar",{**{"— selecione —":None},**cmap}.keys())
        if chosen!="— selecione —":
            item=cmap[chosen]
            with st.form("renamecat"):
                newname=st.text_input("Nome da categoria",item["nome"])
                c1,c2=st.columns(2)
                rename= c1.form_submit_button("Salvar nome")
                activate= c2.form_submit_button("Ativar categoria" if not item["ativo"] else "Desativar categoria")
            if rename:
                result=notify_error(lambda: db.rename_category(uid,item["id"],newname))
                if result is not None: st.success("Categoria atualizada."); st.rerun()
            if activate:
                result=notify_error(lambda: db.toggle_category(uid,item["id"],not bool(item["ativo"])))
                if result is not None: st.success("Status atualizado."); st.rerun()

elif page=="Configurações":
    st.title("Configurações e segurança")
    # CONCEITO: ENTRADA, EVENTO E PERSISTÊNCIA
    # Cada formulário ou botão desta página dispara uma operação específica.
    # Upload de arquivo, checkbox de confirmação e download são componentes
    # que fazem a ponte entre a interface e os dados persistidos.
    with st.form("profile"):
        nome=st.text_input("Nome",u["nome"])
        moeda=st.selectbox("Moeda",["BRL","USD","EUR"],index=["BRL","USD","EUR"].index(u["moeda"]) if u["moeda"] in ["BRL","USD","EUR"] else 0)
        go=st.form_submit_button("Salvar perfil")
    if go:
        result=notify_error(lambda: db.update_profile(uid,nome,moeda))
        if result is not None: st.success("Perfil atualizado."); st.rerun()
    st.subheader("Migrar dados da versão 1")
    st.write("Importa lançamentos e categorias do banco antigo para **este usuário autenticado**, sem apagar nem alterar a base original. Execute uma única vez.")
    default_path=str(db.LEGACY_DB)
    path=st.text_input("Caminho do banco antigo",default_path)
    if u["data_migracao_v1"]: st.info(f"Migração já registrada em {u['data_migracao_v1']}.")
    else:
        if st.button("Verificar e migrar dados da versão 1"):
            result=db.migrate_legacy(uid,path)

            # CONCEITO: EXPRESSÃO CONDICIONAL COM FUNÇÕES
            # A condição escolhe entre st.success e st.error; em seguida, a
            # função escolhida é chamada com a mensagem. Funções são objetos
            # e podem ser passadas/armazenadas como qualquer outro valor.
            (st.success if result["ok"] else st.error)(result["message"])
            if result["ok"]: st.rerun()
    st.subheader("Aparência")
    theme_current=db.get_theme(uid)
    theme_choice=st.selectbox("Tema preferido",["Claro","Escuro"],index=0 if theme_current=="Claro" else 1)
    if st.button("Salvar tema"):
        db.save_theme(uid,theme_choice); st.success("Preferência de tema salva."); st.rerun()
    st.subheader("Backup pessoal")
    st.caption("O backup exporta somente os registros deste usuário. Guarde o arquivo em local privado.")

    # CONCEITO: SAÍDA DE ARQUIVO E F-STRING
    # db.backup_db devolve bytes JSON; st.download_button oferece esses bytes
    # como arquivo. A f-string monta um nome único com o id do usuário.
    st.download_button("Baixar backup dos meus dados (JSON)",db.backup_db(uid),f"finaxis_backup_usuario_{uid}.json","application/json")
    st.warning("O backup contém dados financeiros pessoais. Guarde-o em local privado.")
    st.subheader("Integridade do banco de dados")
    health=db.database_health(uid)
    if health["ok"]:
        st.success("Verificação concluída: estrutura SQLite íntegra e sem erros de chave estrangeira.")
    else:
        st.error("A verificação encontrou possíveis problemas. Faça uma cópia do arquivo do banco e procure suporte antes de restaurar ou excluir dados.")
        st.write({"integrity_check":health["integrity"],"foreign_key_errors":health["foreign_key_errors"]})
    with st.expander("Quantidade de registros da sua conta"):
        show_dataframe(pd.DataFrame([{"Coleção":k.replace("_"," ").title(),"Registros":v} for k,v in health["counts"].items()]),
                     width="stretch",hide_index=True)
    st.subheader("Restaurar backup JSON")

    # CONCEITO: ENTRADA DE ARQUIVO, CONFIRMAÇÃO E EVENTO
    # file_uploader devolve um objeto de arquivo; getvalue() lê seus bytes.
    # A restauração só ocorre quando há arquivo, confirmação marcada e clique.
    st.caption("A restauração é transacional e valida o arquivo antes de gravar. O mesmo arquivo não pode ser importado duas vezes na mesma conta. Faça um backup atual antes de restaurar.")
    uploaded=st.file_uploader("Selecione um backup Finaxis (.json)",type=["json"])
    confirm_restore=st.checkbox("Confirmo que fiz um backup atual e desejo importar os dados deste arquivo.")
    if uploaded and confirm_restore and st.button("Restaurar dados do arquivo"):
        result=notify_error(lambda: db.restore_backup(uid,uploaded.getvalue()))
        if result: st.success(result); st.rerun()
    st.subheader("Atividade recente da conta")
    events=db.audit_events(uid,50)
    if events: show_dataframe(pd.DataFrame([{"Evento":x["evento"],"Detalhe":x["detalhe"],"Data":x["criado_em"]} for x in events]),width="stretch",hide_index=True)
    else: st.caption("Ainda não há eventos registrados.")
    st.subheader("Alterar senha")

    # CONCEITO: FORMULÁRIO, DECISÃO E FUNÇÃO DE ORDEM SUPERIOR
    # A confirmação é comparada antes da chamada ao banco. notify_error recebe
    # uma lambda para centralizar a conversão de exceções em mensagens.
    with st.form("password_change"):
        atual=st.text_input("Senha atual",type="password")
        nova=st.text_input("Nova senha (mínimo 10 caracteres)",type="password")
        conf=st.text_input("Confirmar nova senha",type="password")
        go=st.form_submit_button("Alterar senha")
    if go:
        if nova!=conf:
            st.error("A confirmação não coincide.")
        else:
            result=notify_error(lambda: db.change_password(uid,atual,nova))
            if result:
                db.audit_event(uid,"senha_alterada","Senha atualizada pelo próprio usuário")
                st.success("Senha alterada.")
