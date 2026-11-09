"""Camada de persistência e regras de negócio do Finaxis.

Mapa didático dos conceitos de Python aplicados neste arquivo:

- Tema 2: Python é uma linguagem de alto nível, interpretada, dinâmica e
  multiparadigma. Este módulo usa predominantemente o paradigma
  procedimental, com funções pequenas e reutilizáveis. A biblioteca sqlite3
  é uma extensão implementada em C, acessada por meio da linguagem Python.
- Tema 3: variáveis, tipos de dados, expressões, atribuição e entrada/saída
  (aqui representada por parâmetros, retornos e arquivos JSON).
- Tema 4: decisões, repetições, subprogramas, bibliotecas e tratamento de
  exceções.
- Tema 5: uso de objetos das bibliotecas (Path, Decimal, datetime e
  conexões sqlite3). Não há classes de domínio próprias neste módulo; a
  orientação a objetos aparece no arquivo de testes e nas bibliotecas.

O módulo separa a interface (app.py) das operações de banco. Assim, as
regras de cálculo e persistência podem ser testadas sem abrir a tela.
"""

from __future__ import annotations

# CONCEITO: BIBLIOTECAS E MÓDULOS
# A biblioteca padrão fornece recursos de sistema operacional, banco SQLite,
# criptografia, geração de tokens, manipulação de caminhos, contexto, datas,
# números decimais, JSON e CSV. O import evita reimplementar cada recurso.
import os, sqlite3, hashlib, hmac, secrets, shutil, json, csv
from pathlib import Path
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# CONCEITO: VARIÁVEIS, PATH E EXPRESSÕES
# __file__ é o caminho do arquivo atual. Path.resolve() produz um caminho
# absoluto; .parent obtém a pasta do projeto. os.environ.get permite que uma
# variável de ambiente substitua o caminho padrão do banco.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FINAXIS_DB", BASE_DIR / "data" / "finaxis_v2.db"))
LEGACY_DB = Path(os.environ.get("FINAXIS_V1_DB", BASE_DIR / "data" / "financeiro_v1.db"))

# CONCEITO: TUPLAS COMO CONSTANTES
# Tuplas são sequências imutáveis. Elas guardam os valores aceitos para tipo
# e status e são usadas em validações com o operador in.
TIPOS = ("receita", "despesa")
STATUS = ("pendente", "pago")

# CONCEITO: STRING MULTILINHA
# SCHEMA é uma string enorme, delimitada por três aspas. Ela contém comandos
# SQL que definem tabelas, chaves e índices. O Python apenas armazena o texto;
# o sqlite3 o interpreta quando init_db é executado.
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 moeda TEXT NOT NULL DEFAULT 'BRL', data_migracao_v1 TEXT,
 role TEXT NOT NULL DEFAULT 'user'
);
CREATE TABLE IF NOT EXISTS categories(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 nome TEXT NOT NULL, tipo TEXT NOT NULL CHECK(tipo IN ('receita','despesa')), ativo INTEGER NOT NULL DEFAULT 1,
 UNIQUE(user_id,nome,tipo)
);
CREATE TABLE IF NOT EXISTS accounts(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 nome TEXT NOT NULL, tipo TEXT NOT NULL DEFAULT 'Conta corrente', saldo_inicial TEXT NOT NULL DEFAULT '0.00',
 ativo INTEGER NOT NULL DEFAULT 1, UNIQUE(user_id,nome)
);
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 tipo TEXT NOT NULL CHECK(tipo IN ('receita','despesa','transferencia')),
 descricao TEXT NOT NULL, valor TEXT NOT NULL, data TEXT NOT NULL, categoria TEXT NOT NULL,
 conta TEXT NOT NULL, status TEXT, observacoes TEXT DEFAULT '', transferencia_id TEXT,
 recorrencia_id INTEGER, parcela_atual INTEGER, parcelas_total INTEGER,
 criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id,data);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_recurring_once
 ON transactions(user_id,recorrencia_id,data) WHERE recorrencia_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS budgets(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 categoria TEXT NOT NULL, mes TEXT NOT NULL, limite TEXT NOT NULL,
 UNIQUE(user_id,categoria,mes)
);
CREATE TABLE IF NOT EXISTS cards(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 nome TEXT NOT NULL, limite TEXT NOT NULL, fechamento INTEGER NOT NULL, vencimento INTEGER NOT NULL,
 ativo INTEGER NOT NULL DEFAULT 1, UNIQUE(user_id,nome)
);
CREATE TABLE IF NOT EXISTS card_purchases(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE, descricao TEXT NOT NULL,
 valor_total TEXT NOT NULL, data TEXT NOT NULL, categoria TEXT NOT NULL, parcelas INTEGER NOT NULL DEFAULT 1,
 criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS card_invoice_payments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE, mes_ref TEXT NOT NULL,
 valor TEXT NOT NULL, data_pagamento TEXT NOT NULL, conta TEXT NOT NULL,
 transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL, observacoes TEXT DEFAULT '',
 criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_card_payments_invoice ON card_invoice_payments(user_id,card_id,mes_ref);
CREATE TABLE IF NOT EXISTS recurring(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 tipo TEXT NOT NULL CHECK(tipo IN ('receita','despesa')), descricao TEXT NOT NULL, valor TEXT NOT NULL,
 categoria TEXT NOT NULL, conta TEXT NOT NULL, frequencia TEXT NOT NULL,
 proxima_data TEXT NOT NULL, ativo INTEGER NOT NULL DEFAULT 1, observacoes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS notifications(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 titulo TEXT NOT NULL, mensagem TEXT NOT NULL, chave TEXT NOT NULL, criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 lida INTEGER NOT NULL DEFAULT 0, UNIQUE(user_id,chave)
);
CREATE TABLE IF NOT EXISTS settings(
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, tema TEXT NOT NULL DEFAULT 'Claro',
 moeda TEXT NOT NULL DEFAULT 'BRL', nome_exibicao TEXT
);
CREATE TABLE IF NOT EXISTS login_attempts(
 email TEXT PRIMARY KEY, failures INTEGER NOT NULL DEFAULT 0,
 locked_until TEXT, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 evento TEXT NOT NULL, detalhe TEXT DEFAULT '', criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_user_date ON audit_log(user_id,criado_em);
CREATE TABLE IF NOT EXISTS backup_imports(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 fingerprint TEXT NOT NULL,
 imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id,fingerprint)
);
CREATE TABLE IF NOT EXISTS transaction_submissions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 submission_key TEXT NOT NULL,
 transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id,submission_key)
);
"""

# CONCEITO: LISTA DE TUPLAS
# Cada elemento é uma tupla (nome, tipo). A lista é percorrida por
# executemany para inserir várias categorias iniciais de uma vez.
DEFAULT_CATEGORIES = [
 ("Salário","receita"),("Freelance","receita"),("Investimentos","receita"),("Outros","receita"),
 ("Moradia","despesa"),("Alimentação","despesa"),("Transporte","despesa"),("Saúde","despesa"),
 ("Educação","despesa"),("Lazer","despesa"),("Contas","despesa"),("Outros","despesa")
]
def money(v):
    """Converte valores em Decimal; aceita números e formatos brasileiros como R$ 1.234,56.

    Conceitos aplicados: isinstance, métodos de string, expressão condicional,
    tratamento de exceções, Decimal e arredondamento financeiro. O uso de
    Decimal evita os erros de precisão típicos de float em cálculos monetários.
    """
    # CONCEITO: EXPRESSÃO CONDICIONAL E MÉTODOS DE STRING
    # Se v já for string, remove "R$" e espaços; caso contrário, converte o
    # valor para string. strip, replace e lower são métodos de str.
    raw = str(v).strip().replace("R$", "").replace(" ", "") if isinstance(v, str) else str(v)

    # CONCEITO: DECISÃO E NORMALIZAÇÃO DO FORMATO BRASILEIRO
    # Em "1.234,56", o ponto separa milhares e a vírgula separa decimais.
    # O código troca o ponto por nada e a vírgula por ponto para que Decimal
    # consiga interpretar o número.
    if isinstance(v, str) and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")

    # CONCEITO: TRATAMENTO DE EXCEÇÕES
    # Decimal pode lançar InvalidOperation; o except converte o erro técnico
    # em uma mensagem de negócio compreensível para o usuário.
    try:
        d = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor monetário válido.")
    if not d.is_finite():
        raise ValueError("Valor inválido.")

    # CONCEITO: EXPRESSÃO, ARREDONDAMENTO E RETORNO
    # quantize fixa duas casas decimais e ROUND_HALF_UP define o critério de
    # arredondamento usado em valores monetários.
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def money_str(v):
    """Devolve o valor monetário como texto com duas casas, sem símbolo."""
    # CONCEITO: COMPOSIÇÃO DE FUNÇÕES
    # money_str reaproveita money e formata o Decimal resultante.
    return format(money(v), ".2f")

def fmt(v, currency="BRL"):
    """Formata um valor monetário com o símbolo da moeda escolhida.

    O parâmetro currency tem valor padrão "BRL". O dicionário symbols
    associa códigos de moeda a símbolos; get devolve "R$" quando o código
    não é reconhecido.
    """
    # CONCEITO: DICIONÁRIO, GET E VALOR PADRÃO
    # O dicionário evita uma cadeia longa de if/elif para escolher o símbolo.
    symbols={"BRL":"R$","USD":"US$","EUR":"€"}
    symbol=symbols.get(str(currency or "BRL").upper(),"R$")

    # CONCEITO: F-STRING E MÉTODOS DE STRING
    # A máscara :,.2f usa ponto como separador de milhar e vírgula como
    # decimal. As substituições invertem esses separadores para o padrão
    # brasileiro. "X" é usado como marcador temporário.
    return symbol + " " + f"{money(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@contextmanager
def conn():
    """Abre uma conexão SQLite e garante commit, rollback e fechamento.

    O decorador @contextmanager transforma esta função geradora em um
    gerenciador de contexto. Assim, o código cliente pode usar:
        with conn() as c:
            ...
    O bloco try/except/finally assegura que a transação seja confirmada em
    caso de sucesso, desfeita em caso de erro e que a conexão seja fechada
    sempre, mesmo quando ocorre uma exceção.
    """
    # CONCEITO: PATH E CRIAÇÃO DE DIRETÓRIO
    # mkdir(parents=True, exist_ok=True) cria data/ se necessário e não falha
    # quando a pasta já existe.
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)

    # CONCEITO: OBJETO DE CONEXÃO
    # sqlite3.connect devolve um objeto de conexão. row_factory faz com que
    # cada linha possa ser acessada pelo nome da coluna, como em um dicionário.
    c=sqlite3.connect(DB_PATH,timeout=15)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=15000")

    # CONCEITO: GERADOR, YIELD E CONTEXTO
    # yield entrega a conexão ao bloco with. Quando o bloco termina, a
    # execução continua aqui para confirmar a transação ou desfazê-la.
    try:
        yield c; c.commit()
    except Exception:
        c.rollback(); raise
    finally: c.close()
DEMO_ADMIN_EMAIL = "admin@finaxis.demo"
DEMO_ADMIN_PASSWORD_HASH = "3e1265b985b0320635a7f871e00dacb9:1b6f66dd36d3ee7d6b19846b36c77c5015b73eb05edec3169b585e29e2644c34"


def ensure_demo_admin():
    """Cria a conta de demonstração uma única vez, sempre armazenando hash PBKDF2.

    A função é idempotente: se a conta já existe, apenas garante o perfil
    admin e não redefine a senha. Isso evita que reinicializações apaguem a
    credencial alterada pelo usuário.
    """
    # CONCEITO: SET COMPREHENSION
    # A compreensão com chaves cria um conjunto de nomes de colunas. O
    # operador in verifica se a coluna role já existe antes do ALTER TABLE.
    with conn() as c:
        columns = {row["name"] for row in c.execute("PRAGMA table_info(users)").fetchall()}
        if "role" not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

        # CONCEITO: DECISÃO E RETORNO ANTECIPADO
        row = c.execute("SELECT id FROM users WHERE email=?", (DEMO_ADMIN_EMAIL,)).fetchone()
        if row:
            c.execute("UPDATE users SET role='admin' WHERE id=?", (row["id"],))
            return row["id"]

        # CONCEITO: ATRIBUIÇÃO E CHAMADA DE MÉTODO
        # cur.lastrowid contém o identificador gerado pelo AUTOINCREMENT.
        password_hash = DEMO_ADMIN_PASSWORD_HASH
        cur = c.execute(
            "INSERT INTO users(nome,email,password_hash,role) VALUES(?,?,?,'admin')",
            ("Administrador Demonstração", DEMO_ADMIN_EMAIL, password_hash)
        )
        uid = cur.lastrowid
        c.execute("INSERT INTO settings(user_id,nome_exibicao) VALUES(?,?)",
                  (uid, "Administrador Demonstração"))

        # CONCEITO: LIST COMPREHENSION E EXECUTEMANY
        # A compreensão transforma cada tupla (nome, tipo) em uma nova tupla
        # com o uid. executemany repete o INSERT para toda a lista.
        c.executemany(
            "INSERT INTO categories(user_id,nome,tipo) VALUES(?,?,?)",
            [(uid, nome, tipo) for nome, tipo in DEFAULT_CATEGORIES]
        )
        c.executemany(
            "INSERT INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",
            [(uid, "Conta principal", "Conta corrente", "0.00"),
             (uid, "Carteira", "Carteira", "0.00")]
        )
        return uid


def init_db():
    """Cria as tabelas necessárias e garante a existência da conta demo."""
    # CONCEITO: CONTEXTO E SCRIPT SQL
    # executescript executa vários comandos SQL de uma vez. O with garante
    # commit ao final e rollback se algo falhar.
    with conn() as c:
        c.executescript(SCHEMA)
        columns = {row["name"] for row in c.execute("PRAGMA table_info(users)").fetchall()}
        if "role" not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    ensure_demo_admin()
def hash_password(password, salt=None):
    """Gera um hash PBKDF2-HMAC-SHA256 com salt aleatório.

    Conceitos aplicados: parâmetro com valor padrão, operador or, bytes,
    métodos encode/hex e geração criptograficamente segura de salt com
    secrets.token_bytes. O salt impede que senhas iguais produzam hashes
    iguais. O hash é armazenado no formato "salt:digest".
    """
    if len(password)<10: raise ValueError("A senha deve ter pelo menos 10 caracteres.")

    # CONCEITO: VALOR PADRÃO E OPERADOR LÓGICO
    # Se salt não for informado, o operador or escolhe um novo salt aleatório.
    salt=salt or secrets.token_bytes(16)

    # CONCEITO: FUNÇÃO DE BIBLIOTECA E CODIFICAÇÃO
    # password.encode() transforma o texto em bytes. pbkdf2_hmac aplica
    # 310.000 iterações, tornando a verificação mais custosa para ataques.
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return salt.hex()+":"+digest.hex()

def verify_password(password, encoded):
    """Confere uma senha comparando o hash calculado com o hash armazenado."""
    # CONCEITO: DESEMPACOTAMENTO, HEXADECIMAL E COMPARAÇÃO SEGURA
    # split(":") separa salt e digest. bytes.fromhex reconstrói o salt.
    # hmac.compare_digest evita vazamento de informação por diferença de tempo.
    try:
        salt_hex,digest_hex=encoded.split(":")
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),310000).hex()
        return hmac.compare_digest(actual,digest_hex)
    except Exception: return False

def create_user(nome,email,password):
    """Valida os dados, cria o usuário e inicializa categorias e contas.

    A operação usa uma única conexão e transação: se qualquer INSERT falhar,
    o with desfaz as alterações. O e-mail é normalizado para minúsculas.
    """
    # CONCEITO: MÉTODOS DE STRING E VALIDAÇÃO
    nome=nome.strip(); email=email.strip().lower()
    if not nome: raise ValueError("Informe seu nome.")
    if "@" not in email or "." not in email.split("@")[-1]: raise ValueError("Informe um e-mail válido.")
    ph=hash_password(password)

    # CONCEITO: TRANSAÇÃO, EXCEÇÃO ESPECÍFICA E EXECUTEMANY
    # IntegrityError indica violação de unicidade (e-mail repetido). O erro
    # é convertido em ValueError com mensagem de negócio.
    with conn() as c:
        try:
            cur=c.execute("INSERT INTO users(nome,email,password_hash) VALUES(?,?,?)",(nome,email,ph))
        except sqlite3.IntegrityError: raise ValueError("Este e-mail já está cadastrado.")
        uid=cur.lastrowid
        c.execute("INSERT INTO settings(user_id,nome_exibicao) VALUES(?,?)",(uid,nome))
        c.executemany("INSERT INTO categories(user_id,nome,tipo) VALUES(?,?,?)",[(uid,n,t) for n,t in DEFAULT_CATEGORIES])
        c.executemany("INSERT INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",[
            (uid,"Conta principal","Conta corrente","0.00"),(uid,"Carteira","Carteira","0.00")])
    return uid
def login_locked(email):
    """Informa se o e-mail está temporariamente bloqueado por tentativas falhas.

    O código compara datas com datetime/timedelta e limpa registros antigos.
    A conversão de texto ISO para datetime é protegida por try/except porque
    valores antigos ou corrompidos não devem quebrar o login.
    """
    # CONCEITO: NORMALIZAÇÃO E DATAS
    key=(email or "").strip().lower()
    now=datetime.now()
    with conn() as c:
        row=c.execute("SELECT failures,locked_until,updated_at FROM login_attempts WHERE email=?",(key,)).fetchone()
        if not row:
            return False
        # Ao terminar o bloqueio, reinicia a janela de tentativas.
        if row["locked_until"]:
            try:
                if datetime.fromisoformat(row["locked_until"]) > now:
                    return True
            except (TypeError, ValueError):
                pass
            c.execute("DELETE FROM login_attempts WHERE email=?",(key,))
            return False
        # Tentativas antigas não devem permanecer acumuladas indefinidamente.
        try:
            updated=datetime.fromisoformat(row["updated_at"])
            if now-updated > timedelta(minutes=15):
                c.execute("DELETE FROM login_attempts WHERE email=?",(key,))
        except (TypeError, ValueError):
            c.execute("DELETE FROM login_attempts WHERE email=?",(key,))
    return False


def register_login_failure(email, max_failures=5, lock_minutes=15):
    """Registra uma falha e calcula quando o bloqueio deve terminar.

    max_failures e lock_minutes possuem valores padrão. O retorno é uma
    tupla (quantidade de falhas, indicador de bloqueio).
    """
    # CONCEITO: PARÂMETROS PADRÃO E DATA/HORA
    key=(email or "").strip().lower()
    now=datetime.now()
    with conn() as c:
        row=c.execute("SELECT failures,updated_at,locked_until FROM login_attempts WHERE email=?",(key,)).fetchone()
        failures=0
        if row and not row["locked_until"]:
            try:
                updated=datetime.fromisoformat(row["updated_at"])
                if now-updated <= timedelta(minutes=15):
                    failures=int(row["failures"])
            except (TypeError, ValueError):
                failures=0
        failures += 1
        locked=(now+timedelta(minutes=lock_minutes)).isoformat(timespec="seconds") if failures>=max_failures else None
        c.execute("""INSERT INTO login_attempts(email,failures,locked_until,updated_at)
          VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET
          failures=excluded.failures,locked_until=excluded.locked_until,updated_at=excluded.updated_at""",
          (key,failures,locked,now.isoformat(timespec="seconds")))
    return failures, bool(locked)


def clear_login_failures(email):
    """Remove o histórico de falhas do e-mail, liberando novas tentativas."""
    with conn() as c:
        c.execute("DELETE FROM login_attempts WHERE email=?",((email or "").strip().lower(),))


def authenticate(email,password):
    """Verifica credenciais e devolve os dados do usuário autenticado, ou None.

    A função combina decisão, chamada de subprogramas e isolamento:
    login_locked verifica o bloqueio; verify_password compara o hash;
    register_login_failure contabiliza erros.
    """
    # CONCEITO: DECISÃO E RETORNO ANTECIPADO
    key=(email or "").strip().lower()
    if login_locked(key):
        return None
    with conn() as c:
        row=c.execute("SELECT * FROM users WHERE email=?",(key,)).fetchone()

    # CONCEITO: OPERADOR LÓGICO AND E CONVERSÃO DE sqlite3.Row
    # row é um objeto sqlite3.Row; dict(row) o converte em dicionário comum.
    if row and verify_password(password,row["password_hash"]):
        clear_login_failures(key)
        return dict(row)
    register_login_failure(key)
    return None


def change_password(uid, current_password, new_password):
    """Troca a senha somente após confirmar a senha atual.

    O novo hash é gerado pela mesma função usada no cadastro. A validação de
    tamanho fica centralizada em hash_password.
    """
    with conn() as c:
        row=c.execute("SELECT password_hash FROM users WHERE id=?",(uid,)).fetchone()
        if not row:
            raise ValueError("Usuário não encontrado.")
        if not verify_password(current_password,row["password_hash"]):
            raise ValueError("Senha atual incorreta.")
        new_hash=hash_password(new_password)
        c.execute("UPDATE users SET password_hash=? WHERE id=?",(new_hash,uid))
    return True

def audit_event(uid, evento, detalhe=""):
    """Registra um evento de auditoria associado ao usuário."""
    # CONCEITO: SLICING DE STRING
    # str(detalhe)[:500] limita o texto a 500 caracteres antes de gravar.
    with conn() as c: c.execute("INSERT INTO audit_log(user_id,evento,detalhe) VALUES(?,?,?)",(uid,evento,str(detalhe)[:500]))

def audit_events(uid, limit=100):
    """Devolve os eventos mais recentes, limitados a no máximo 500."""
    # CONCEITO: LIST COMPREHENSION E FUNÇÕES max/min
    # A expressão max(1,min(int(limit),500)) mantém o limite entre 1 e 500.
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT evento,detalhe,criado_em FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT ?",(uid,max(1,min(int(limit),500)))).fetchall()]

def mark_all_notifications_read(uid):
    """Marca como lidas todas as notificações não lidas do usuário."""
    with conn() as c: return c.execute("UPDATE notifications SET lida=1 WHERE user_id=? AND lida=0",(uid,)).rowcount

def user(uid):
    """Busca os dados públicos do usuário pelo identificador."""
    with conn() as c: r=c.execute("SELECT id,nome,email,moeda,data_migracao_v1,role FROM users WHERE id=?",(uid,)).fetchone()
    return dict(r) if r else None

def update_profile(uid,nome,moeda):
    """Atualiza nome e moeda do usuário e da tabela de configurações."""
    if not nome.strip(): raise ValueError("Informe o nome.")
    with conn() as c:
        c.execute("UPDATE users SET nome=?,moeda=? WHERE id=?",(nome.strip(),moeda,uid))
        c.execute("UPDATE settings SET nome_exibicao=?,moeda=? WHERE user_id=?",(nome.strip(),moeda,uid))

def categories(uid,tipo=None):
    """Lista categorias ativas; se tipo for informado, filtra por receita/despesa."""
    with conn() as c:
        # CONCEITO: PARÂMETRO OPCIONAL E DECISÃO
        # tipo=None indica que não há filtro. A presença de um valor escolhe
        # a consulta mais específica.
        if tipo: rows=c.execute("SELECT * FROM categories WHERE user_id=? AND tipo=? AND ativo=1 ORDER BY nome",(uid,tipo)).fetchall()
        else: rows=c.execute("SELECT * FROM categories WHERE user_id=? ORDER BY tipo,nome",(uid,)).fetchall()
    return [dict(r) for r in rows]

def add_category(uid,nome,tipo):
    """Valida e cadastra uma categoria do usuário."""
    if tipo not in TIPOS or not nome.strip(): raise ValueError("Informe nome e tipo válidos.")
    with conn() as c:
        try: c.execute("INSERT INTO categories(user_id,nome,tipo) VALUES(?,?,?)",(uid,nome.strip(),tipo))
        except sqlite3.IntegrityError: raise ValueError("Categoria já existe.")

def rename_category(uid,cid,nome):
    """Renomeia a categoria e propaga o novo nome para lançamentos e orçamentos."""
    with conn() as c:
        row=c.execute("SELECT nome,tipo FROM categories WHERE id=? AND user_id=?",(cid,uid)).fetchone()
        if not row: raise ValueError("Categoria não encontrada.")
        try:
            # CONCEITO: TRANSAÇÃO COM VÁRIAS ATUALIZAÇÕES
            # O with mantém as três alterações juntas: se uma falhar, todas
            # são desfeitas pelo rollback.
            c.execute("UPDATE categories SET nome=? WHERE id=? AND user_id=?",(nome.strip(),cid,uid))
            c.execute("UPDATE transactions SET categoria=? WHERE user_id=? AND categoria=?",(nome.strip(),uid,row["nome"]))
            c.execute("UPDATE budgets SET categoria=? WHERE user_id=? AND categoria=?",(nome.strip(),uid,row["nome"]))
        except sqlite3.IntegrityError: raise ValueError("Já existe uma categoria com esse nome.")

def toggle_category(uid,cid,active):
    """Ativa ou desativa uma categoria do usuário."""
    with conn() as c:
        # CONCEITO: EXPRESSÃO CONDICIONAL
        # 1 if active else 0 converte o booleano para o inteiro usado no SQLite.
        cur=c.execute("UPDATE categories SET ativo=? WHERE id=? AND user_id=?",(1 if active else 0,cid,uid))
        if cur.rowcount==0: raise ValueError("Categoria não encontrada.")

def save_theme(uid,tema):
    """Persiste a preferência de tema do usuário."""
    if tema not in ("Claro","Escuro"): raise ValueError("Tema inválido.")
    with conn() as c: c.execute("UPDATE settings SET tema=? WHERE user_id=?",(tema,uid))

def get_theme(uid):
    """Lê o tema salvo; devolve Claro quando não há configuração."""
    with conn() as c:
        row=c.execute("SELECT tema FROM settings WHERE user_id=?",(uid,)).fetchone()
    return row["tema"] if row else "Claro"

def add_account(uid,nome,tipo,saldo):
    """Cadastra uma conta com saldo inicial convertido para texto monetário."""
    if not nome.strip(): raise ValueError("Informe o nome da conta.")
    with conn() as c:
        try: c.execute("INSERT INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",(uid,nome.strip(),tipo,money_str(saldo)))
        except sqlite3.IntegrityError: raise ValueError("Já existe uma conta com esse nome.")

def accounts(uid):
    """Saldo atual: saldo inicial + receitas - despesas pagas +/- transferências.

    O código demonstra dicionário, setdefault, laços for, if/elif e
    acumulação com Decimal. A lista by_account agrupa os lançamentos por
    conta antes de calcular cada saldo.
    """
    with conn() as c:
        rows=c.execute("SELECT * FROM accounts WHERE user_id=? AND ativo=1 ORDER BY nome",(uid,)).fetchall()
        tx_rows=c.execute("SELECT conta,tipo,valor,status FROM transactions WHERE user_id=?",(uid,)).fetchall()

    # CONCEITO: DICIONÁRIO DE LISTAS E SETDEFAULT
    # setdefault cria uma lista vazia na primeira ocorrência de cada conta.
    # Depois, append acrescenta os lançamentos daquela conta.
    by_account={}
    for t in tx_rows:
        by_account.setdefault(t["conta"], []).append(t)

    result=[]
    for r in rows:
        d=dict(r); d["saldo"]=money(d["saldo_inicial"])

        # CONCEITO: REPETIÇÃO E DECISÕES ENCADEADAS
        # Cada tipo de lançamento altera o saldo de forma diferente. O método
        # get evita KeyError quando a conta ainda não tem movimentações.
        for t in by_account.get(d["nome"], []):
            v=money(t["valor"])
            if t["tipo"]=="receita": d["saldo"] += v
            elif t["tipo"]=="despesa" and t["status"]=="pago": d["saldo"] -= v
            elif t["tipo"]=="transferencia":
                if (t["status"] or "") == "entrada": d["saldo"] += v
                elif (t["status"] or "") == "saida": d["saldo"] -= v
        result.append(d)
    return result
def add_transaction(uid,tipo,descricao,valor,data_lancamento,categoria,conta,status=None,observacoes="", transferencia_id=None, parcela_atual=None, parcelas_total=None, submission_key=None):
    """Valida e insere um lançamento de receita, despesa ou transferência.

    Conceitos aplicados: parâmetros com valores padrão, validação com if,
    conversão de data com date.fromisoformat, expressão condicional,
    transação e proteção contra envio duplicado usando submission_key.
    """
    # CONCEITO: VALIDAÇÃO E CONVERSÃO DE TIPOS
    if tipo not in ("receita","despesa","transferencia"): raise ValueError("Tipo inválido.")
    if not descricao.strip() or not categoria.strip() or not conta.strip(): raise ValueError("Preencha descrição, categoria e conta.")
    valor=money(valor)
    if valor<=0: raise ValueError("O valor deve ser maior que zero.")

    # CONCEITO: TRATAMENTO DE EXCEÇÃO DE CONVERSÃO
    try: d=date.fromisoformat(str(data_lancamento)).isoformat()
    except ValueError: raise ValueError("Data inválida.")

    # CONCEITO: DECISÕES ENCADEADAS PARA NORMALIZAR STATUS
    if tipo=="despesa": status=status if status in STATUS else "pendente"
    elif tipo=="transferencia": status=status if status in ("entrada","saida") else None
    else: status=None

    with conn() as c:
        # CONCEITO: IDEMPOTÊNCIA
        # Se a mesma submission_key já foi usada, devolve o lançamento
        # existente em vez de criar outro.
        if submission_key:
            previous=c.execute("SELECT transaction_id FROM transaction_submissions WHERE user_id=? AND submission_key=?",
                               (uid,str(submission_key))).fetchone()
            if previous:
                return previous["transaction_id"]
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone(): raise ValueError("Conta não encontrada.")
        if tipo in TIPOS and not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo=? AND ativo=1",(uid,categoria,tipo)).fetchone():
            raise ValueError("Categoria inválida para este tipo.")
        cur=c.execute("""INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id,parcela_atual,parcelas_total)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(uid,tipo,descricao.strip(),str(valor),d,categoria,conta,status,observacoes.strip(),transferencia_id,parcela_atual,parcelas_total))
        if submission_key:
            c.execute("INSERT INTO transaction_submissions(user_id,submission_key,transaction_id) VALUES(?,?,?)",
                      (uid,str(submission_key),cur.lastrowid))
        return cur.lastrowid

def list_transactions(uid, filtros=None):
    """Lista lançamentos aplicando filtros opcionais e parâmetros SQL.

    A consulta é montada dinamicamente: cada filtro acrescenta uma condição
    ao SQL e um valor à lista p. Os valores nunca são concatenados no texto,
    pois são enviados como parâmetros para evitar SQL injection.
    """
    # CONCEITO: DICIONÁRIO OPCIONAL E LISTA DE PARÂMETROS
    filtros=filtros or {}; sql="SELECT * FROM transactions WHERE user_id=?"; p=[uid]
    for key, col in [("tipo","tipo"),("categoria","categoria"),("conta","conta")]:
        v=filtros.get(key)
        if v and v!="Todos": sql+=f" AND {col}=?"; p.append(v)
    status=filtros.get("status")
    if status and status!="Todos":
        if status=="Concluído": sql+=" AND (status IS NULL OR status='')"
        else: sql+=" AND status=?"; p.append(status)
    if filtros.get("inicio"): sql+=" AND data>=?"; p.append(str(filtros["inicio"]))
    if filtros.get("fim"): sql+=" AND data<=?"; p.append(str(filtros["fim"]))

    # CONCEITO: F-STRING E MÉTODOS DE LISTA
    # extend acrescenta os dois parâmetros de busca de uma só vez.
    if filtros.get("busca"): sql+=" AND (descricao LIKE ? OR observacoes LIKE ?)"; p.extend([f"%{filtros['busca']}%",f"%{filtros['busca']}%"])
    sql+=" ORDER BY data DESC,id DESC"
    with conn() as c: return [dict(r) for r in c.execute(sql,p).fetchall()]
def delete_transaction(uid,tid):
    """Exclui um lançamento e, quando aplicável, as duas pontas da transferência."""
    with conn() as c:
        row=c.execute("SELECT transferencia_id FROM transactions WHERE id=? AND user_id=?",(tid,uid)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        # Ao excluir um pagamento de fatura, desfaz também a baixa registrada na fatura.
        c.execute("DELETE FROM card_invoice_payments WHERE user_id=? AND transaction_id=?",(uid,tid))
        if row["transferencia_id"]:
            c.execute("DELETE FROM transactions WHERE user_id=? AND transferencia_id=?",(uid,row["transferencia_id"]))
        else:
            c.execute("DELETE FROM transactions WHERE id=? AND user_id=?",(tid,uid))
def edit_transaction(uid,tid,descricao,valor,data_lancamento,categoria,conta,status,observacoes):
    """Edita um lançamento existente, preservando regras de tipo e par de transferência."""
    valor=money(valor)
    if valor<=0: raise ValueError("O valor deve ser maior que zero.")
    descricao=(descricao or "").strip()
    if not descricao: raise ValueError("Informe a descrição do lançamento.")
    d=date.fromisoformat(str(data_lancamento)).isoformat()
    with conn() as c:
        r=c.execute("SELECT * FROM transactions WHERE id=? AND user_id=?",(tid,uid)).fetchone()
        if not r: raise ValueError("Lançamento não encontrado.")
        if c.execute("SELECT 1 FROM card_invoice_payments WHERE user_id=? AND transaction_id=?",(uid,tid)).fetchone():
            raise ValueError("Este lançamento é um pagamento de fatura; exclua-o pela área de lançamentos para estornar também a fatura.")
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone():
            raise ValueError("Conta não encontrada.")
        if r["tipo"] in TIPOS and not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo=? AND ativo=1",(uid,categoria,r["tipo"])).fetchone():
            raise ValueError("Categoria inválida para este tipo.")
        new_status=status if r["tipo"]=="despesa" and status in STATUS else (r["status"] if r["tipo"]=="despesa" else r["status"])
        if r["tipo"]=="transferencia":
            if not r["transferencia_id"]: raise ValueError("Transferência sem identificador de par; não é seguro editá-la.")
            pair=c.execute("SELECT id FROM transactions WHERE user_id=? AND transferencia_id=?",(uid,r["transferencia_id"])).fetchall()
            if len(pair)!=2: raise ValueError("O par da transferência está incompleto. Exclua e registre novamente.")
            c.execute("UPDATE transactions SET descricao=?,valor=?,data=?,observacoes=? WHERE user_id=? AND transferencia_id=?",
                      (descricao,str(valor),d,(observacoes or "").strip(),uid,r["transferencia_id"]))
        else:
            c.execute("""UPDATE transactions SET descricao=?,valor=?,data=?,categoria=?,conta=?,status=?,observacoes=?
            WHERE id=? AND user_id=?""",(descricao,str(valor),d,categoria,conta,new_status,(observacoes or "").strip(),tid,uid))
def summary(uid, inicio=None, fim=None):
    """Soma receitas, despesas pagas e pendências no período informado.

    Conceitos aplicados: expressão geradora, função sum com valor inicial
    Decimal e dicionário como retorno estruturado.
    """
    rows=list_transactions(uid,{"inicio":inicio,"fim":fim})

    # CONCEITO: EXPRESSÕES GERADORAS
    # Cada sum percorre rows sem criar uma lista intermediária. O segundo
    # argumento money(0) define o valor inicial e mantém o tipo Decimal.
    rec=sum((money(r["valor"]) for r in rows if r["tipo"]=="receita"),money(0))
    desp=sum((money(r["valor"]) for r in rows if r["tipo"]=="despesa" and r["status"]=="pago"),money(0))
    pend=sum((money(r["valor"]) for r in rows if r["tipo"]=="despesa" and r["status"]=="pendente"),money(0))
    return {"receitas":rec,"despesas_pagas":desp,"pendentes":pend,"saldo":rec-desp}
def add_budget(uid,categoria,mes,limite):
    """Cria ou atualiza o orçamento mensal de uma categoria de despesa."""
    limite=money(limite)
    if limite<=0: raise ValueError("Limite deve ser positivo.")
    try: mes=date.fromisoformat(str(mes)+"-01").strftime("%Y-%m")
    except ValueError: raise ValueError("Mês inválido; use AAAA-MM.")
    with conn() as c:
        if not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo='despesa'",(uid,categoria)).fetchone():
            raise ValueError("Categoria de despesa não encontrada.")
        c.execute("""INSERT INTO budgets(user_id,categoria,mes,limite) VALUES(?,?,?,?)
        ON CONFLICT(user_id,categoria,mes) DO UPDATE SET limite=excluded.limite""",(uid,categoria,mes,str(limite)))
def budgets(uid,mes):
    """Lista orçamentos e calcula o gasto pago de cada categoria no mês."""
    with conn() as c:
        rows=c.execute("SELECT * FROM budgets WHERE user_id=? AND mes=? ORDER BY categoria",(uid,mes)).fetchall()
        tx=c.execute("SELECT categoria,valor FROM transactions WHERE user_id=? AND tipo='despesa' AND status='pago' AND substr(data,1,7)=?",(uid,mes)).fetchall()
    # CONCEITO: ACUMULADOR EM DICIONÁRIO
    # get devolve Decimal(0) quando a categoria ainda não apareceu. O valor
    # anterior é somado ao lançamento atual.
    spent_by_category={}
    for t in tx: spent_by_category[t["categoria"]]=spent_by_category.get(t["categoria"],money(0))+money(t["valor"])

    # CONCEITO: LISTA DE DICIONÁRIOS
    # Cada linha do banco é convertida em dict e enriquecida com os campos
    # gasto e limite_valor antes de entrar na lista de saída.
    out=[]
    for r in rows:
        d=dict(r); d["gasto"]=spent_by_category.get(d["categoria"],money(0)); d["limite_valor"]=money(d["limite"]); out.append(d)
    return out
def add_card(uid,nome,limite,fechamento,vencimento):
    """Cadastra um cartão com limite e dias de fechamento/vencimento válidos."""
    nome=(nome or "").strip(); limite=money(limite)
    if not nome or limite<=0 or not 1<=int(fechamento)<=28 or not 1<=int(vencimento)<=28:
        raise ValueError("Informe nome, limite positivo e dias válidos (1 a 28).")
    with conn() as c:
        try: c.execute("INSERT INTO cards(user_id,nome,limite,fechamento,vencimento) VALUES(?,?,?,?,?)",(uid,nome,str(limite),int(fechamento),int(vencimento)))
        except sqlite3.IntegrityError: raise ValueError("Cartão já cadastrado.")
def cards(uid):
    """Lista os cartões ativos do usuário."""
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM cards WHERE user_id=? AND ativo=1 ORDER BY nome",(uid,)).fetchall()]

def add_purchase(uid,card_id,descricao,valor,data_lancamento,categoria,parcelas):
    """Registra uma compra de cartão e valida cartão, categoria e parcelas."""
    valor=money(valor); parcelas=int(parcelas); descricao=(descricao or "").strip()
    if not descricao: raise ValueError("Informe a descrição da compra.")
    if valor<=0 or parcelas<1 or parcelas>60: raise ValueError("Valor ou número de parcelas inválido.")
    dt=date.fromisoformat(str(data_lancamento)).isoformat()
    with conn() as c:
        if not c.execute("SELECT 1 FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone(): raise ValueError("Cartão inválido.")
        if not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo='despesa' AND ativo=1",(uid,categoria)).fetchone(): raise ValueError("Categoria de despesa inválida.")
        c.execute("INSERT INTO card_purchases(user_id,card_id,descricao,valor_total,data,categoria,parcelas) VALUES(?,?,?,?,?,?,?)",(uid,card_id,descricao,str(valor),dt,categoria,parcelas))
def purchases(uid):
    """Lista compras de cartão junto com dados do cartão via JOIN."""
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT p.*,c.nome cartao,c.limite,c.fechamento,c.vencimento FROM card_purchases p JOIN cards c ON c.id=p.card_id WHERE p.user_id=? ORDER BY p.data DESC",(uid,)).fetchall()]

def _add_month(year, month, offset=1):
    """Soma meses usando aritmética inteira, sem depender de datas fixas."""
    # CONCEITO: DIVISÃO INTEIRA E RESTO
    # index//12 e index%12+1 convertem o total de meses de volta em ano/mês.
    index=year*12+(month-1)+offset
    return index//12, index%12+1

def _invoice_month(purchase_date, closing_day):
    """Determina o mês de fatura conforme o dia de fechamento do cartão."""
    d=date.fromisoformat(str(purchase_date)); y,m=d.year,d.month
    if d.day>int(closing_day): y,m=_add_month(y,m,1)
    return y,m

def _installment_values(total, count):
    """Divide o total em parcelas de centavos, distribuindo o resto nas primeiras."""
    # CONCEITO: DIVMOD E LIST COMPREHENSION
    # divmod devolve quociente e resto em uma única operação. O resto é
    # distribuído como um centavo extra nas primeiras parcelas. enumerate/
    # index i permite essa distribuição, e Decimal evita erro de arredondamento.
    cents=int(money(total)*100); base,extra=divmod(cents,count)
    return [Decimal(base+(1 if i<extra else 0))/Decimal(100) for i in range(count)]
def card_invoice(uid, card_id, mes_ref):
    """Calcula fatura do mês de fechamento e o vencimento no mês seguinte.

    Conceitos aplicados: desempacotamento, map/int, validação de data,
    laços aninhados, enumerate, compreensão de lista, geradores e o
    dicionário final com total, pago e valor em aberto.
    """
    # CONCEITO: DESEMPACOTAMENTO E CONVERSÃO
    # split separa "AAAA-MM"; map(int, ...) converte as duas partes. A
    # chamada date(...) valida o mês e dispara exceção se for inválido.
    try: year,month=map(int,mes_ref.split("-")); date(year,month,1)
    except Exception: raise ValueError("Mês da fatura inválido; use AAAA-MM.")
    with conn() as c:
        card=c.execute("SELECT * FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone()
        if not card: raise ValueError("Cartão não encontrado.")
        rows=c.execute("SELECT * FROM card_purchases WHERE user_id=? AND card_id=?",(uid,card_id)).fetchall()
        payments=c.execute("SELECT valor FROM card_invoice_payments WHERE user_id=? AND card_id=? AND mes_ref=?",(uid,card_id,mes_ref)).fetchall()
    lines=[]; total=money(0)

    # CONCEITO: LAÇOS ANINHADOS E ENUMERATE
    # O primeiro for percorre compras; o segundo percorre as parcelas com
    # índice. enumerate fornece index e amount ao mesmo tempo.
    for purchase in rows:
        sy,sm=_invoice_month(purchase["data"],card["fechamento"])
        values=_installment_values(purchase["valor_total"],int(purchase["parcelas"]))
        for index,amount in enumerate(values):
            iy,im=_add_month(sy,sm,index)
            if (iy,im)==(year,month):
                lines.append({"compra_id":purchase["id"],"descricao":purchase["descricao"],"categoria":purchase["categoria"],"data_compra":purchase["data"],"parcela":index+1,"parcelas":int(purchase["parcelas"]),"valor":amount})
                total+=amount

    paid=sum((money(row["valor"]) for row in payments),money(0))
    due_year,due_month=_add_month(year,month,1)

    # CONCEITO: IMPORTAÇÃO LOCAL E FUNÇÕES DE BIBLIOTECA
    # calendar.monthrange informa o último dia do mês. min impede vencimento
    # em dia inexistente (por exemplo, 31 em fevereiro).
    import calendar
    due_day=min(int(card["vencimento"]),calendar.monthrange(due_year,due_month)[1])

    # CONCEITO: DICIONÁRIO COMO REGISTRO COMPOSTO
    # O retorno reúne dados do cartão, itens calculados e totais. max evita
    # valor em aberto negativo.
    return {"cartao":card["nome"],"card_id":card_id,"mes_ref":mes_ref,"vencimento":date(due_year,due_month,due_day).isoformat(),"itens":lines,"total":total,"pago":paid,"aberto":max(money(0),total-paid),"limite":money(card["limite"])}
def pay_card_invoice(uid, card_id, mes_ref, valor, conta, data_pagamento=None, observacoes=""):
    """Baixa uma fatura e registra a saída na conta escolhida, numa única transação.

    Conceitos aplicados: valor padrão None, operador or para escolher a data
    atual, validações e transação com dois INSERTs. Se o segundo falhar, o
    primeiro também é desfeito pelo rollback de conn().
    """
    # CONCEITO: OPERADOR OR E DATA PADRÃO
    # data_pagamento or date.today().isoformat() usa hoje quando o parâmetro
    # não foi informado.
    value=money(valor); paid_date=date.fromisoformat(str(data_pagamento or date.today().isoformat())).isoformat()
    if value<=0: raise ValueError("O pagamento deve ser maior que zero.")
    with conn() as c:
        card=c.execute("SELECT * FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone()
        if not card: raise ValueError("Cartão não encontrado.")
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone(): raise ValueError("Conta de pagamento não encontrada.")
        invoice=card_invoice(uid,card_id,mes_ref)
        if value>invoice["aberto"]: raise ValueError("O pagamento não pode ser maior que o saldo em aberto da fatura.")
        c.execute("INSERT OR IGNORE INTO categories(user_id,nome,tipo) VALUES(?,?,'despesa')",(uid,"Pagamento de cartão"))
        cur=c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes) VALUES(?,?,?,?,?,?,?,?,?)",
            (uid,"despesa",f"Pagamento fatura {card['nome']} ({mes_ref})",str(value),paid_date,"Pagamento de cartão",conta,"pago",(observacoes or "").strip()))
        txid=cur.lastrowid
        c.execute("INSERT INTO card_invoice_payments(user_id,card_id,mes_ref,valor,data_pagamento,conta,transaction_id,observacoes) VALUES(?,?,?,?,?,?,?,?)",
            (uid,card_id,mes_ref,str(value),paid_date,conta,txid,(observacoes or "").strip()))
    return card_invoice(uid,card_id,mes_ref)
def card_outstanding(uid, card_id):
    """Soma o valor ainda aberto das faturas futuras e do mês atual."""
    with conn() as c:
        card=c.execute("SELECT fechamento FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone()
        rows=c.execute("SELECT data,parcelas,valor_total FROM card_purchases WHERE user_id=? AND card_id=?",(uid,card_id)).fetchall()
    if not card: raise ValueError("Cartão não encontrado.")
    # CONCEITO: CONJUNTO, RANGE E F-STRING COM FORMATAÇÃO
    # set elimina meses repetidos. range percorre as parcelas. :04d e :02d
    # garantem quatro e dois dígitos, respectivamente.
    months=set()
    for purchase in rows:
        y,m=_invoice_month(purchase["data"],card["fechamento"])
        for offset in range(int(purchase["parcelas"])):
            yy,mm=_add_month(y,m,offset); months.add(f"{yy:04d}-{mm:02d}")
    current=date.today().strftime("%Y-%m")

    # CONCEITO: EXPRESSÃO GERADORA, SORTED E COMPARAÇÃO DE STRINGS
    # Como o formato é AAAA-MM, a comparação lexicográfica equivale à
    # comparação cronológica.
    return sum((card_invoice(uid,card_id,month)["aberto"] for month in sorted(months) if month>=current),money(0))
def add_transfer(uid,descricao,valor,data_lancamento,origem,destino):
    """Registra as duas pontas de uma transferência atomicamente.

    Conceitos aplicados: operador or, validação de contas distintas, geração
    de identificador com secrets, laço for sobre tupla e transação com dois
    INSERTs que precisam existir juntos.
    """
    descricao=(descricao or "").strip(); value=money(valor); dt=date.fromisoformat(str(data_lancamento)).isoformat()
    if not descricao: raise ValueError("Informe a descrição da transferência.")
    if value<=0: raise ValueError("O valor deve ser maior que zero.")
    if origem==destino: raise ValueError("Origem e destino devem ser diferentes.")
    transfer_id=secrets.token_hex(16)
    with conn() as c:
        # CONCEITO: REPETIÇÃO SOBRE TUPLA E F-STRING
        # As duas contas são validadas antes de qualquer INSERT. Se uma não
        # existir, a mensagem inclui o nome usando f-string.
        for account in (origem,destino):
            if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,account)).fetchone(): raise ValueError(f"Conta não encontrada: {account}.")

        # CONCEITO: TRANSAÇÃO ATÔMICA
        # Saída e entrada compartilham transferencia_id. O commit só ocorre
        # no final do with; se um INSERT falhar, nenhum dos dois é gravado.

        c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,"transferencia",descricao,str(value),dt,"Transferência",origem,"saida","Saída da transferência",transfer_id))
        c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,"transferencia",descricao,str(value),dt,"Transferência",destino,"entrada","Entrada da transferência",transfer_id))
    return transfer_id

def add_recurring(uid,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,observacoes=""):
    """Cadastra uma recorrência validando tipo, frequência, valor e vínculos."""
    if tipo not in TIPOS or frequencia not in ("Diária","Semanal","Mensal","Anual"): raise ValueError("Tipo ou frequência inválida.")
    dt=date.fromisoformat(str(proxima_data)).isoformat(); valor=money(valor); descricao=(descricao or "").strip()
    if not descricao: raise ValueError("Informe a descrição da recorrência.")
    if valor<=0: raise ValueError("Valor deve ser positivo.")
    with conn() as c:
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone(): raise ValueError("Conta não encontrada.")
        if not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo=? AND ativo=1",(uid,categoria,tipo)).fetchone(): raise ValueError("Categoria inválida para o tipo escolhido.")
        c.execute("INSERT INTO recurring(user_id,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,observacoes) VALUES(?,?,?,?,?,?,?,?,?)",(uid,tipo,descricao,str(valor),categoria,conta,frequencia,dt,(observacoes or "").strip()))

def recurrings(uid):
    """Lista as recorrências do usuário em ordem de próxima data."""
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM recurring WHERE user_id=? ORDER BY proxima_data",(uid,)).fetchall()]

def _recurrence_date(anchor, frequency, occurrence_index):
    """Calcula a ocorrência a partir da data-âncora, evitando deriva em meses curtos.

    Conceitos aplicados: if/elif encadeados, timedelta, aritmética de datas,
    calendar.monthrange e min para ajustar dias inexistentes. A âncora evita
    que uma recorrência do dia 31 "escorregue" para o dia 28 nos meses
    seguintes.
    """
    import calendar

    # CONCEITO: DECISÕES ENCADEADAS E timedelta
    # Diária e Semanal usam deslocamentos fixos em dias. Anual e Mensal
    # precisam ajustar o dia ao último dia válido do mês de destino.
    if frequency == "Diária":
        return anchor + timedelta(days=occurrence_index)
    if frequency == "Semanal":
        return anchor + timedelta(days=7 * occurrence_index)
    if frequency == "Anual":
        year = anchor.year + occurrence_index
        day = min(anchor.day, calendar.monthrange(year, anchor.month)[1])
        return date(year, anchor.month, day)
    year, month = _add_month(anchor.year, anchor.month, occurrence_index)
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def run_recurring(uid, max_occurrences_per_recurring=500):
    """Gera ocorrências vencidas com limite por recorrência e calendário ancorado.

    Conceitos aplicados: parâmetro com valor padrão, acumuladores, laços
    while, None como ausência de valor, expressão condicional, INSERT OR
    IGNORE e atualização da próxima data dentro da mesma transação.
    """
    today = date.today()
    created = 0

    # CONCEITO: FUNÇÕES max E min PARA LIMITAR ENTRADA
    # O limite fica entre 1 e 5000, independentemente do valor recebido.
    cap = max(1, min(int(max_occurrences_per_recurring), 5000))
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM recurring WHERE user_id=? AND ativo=1 AND proxima_data<=?",
            (uid, today.isoformat())
        ).fetchall()
        for r in rows:
            due = date.fromisoformat(r["proxima_data"])
            # A primeira data cadastrada é a âncora. Depois, usa o primeiro lançamento
            # gerado para a recorrência, se existir, para manter o dia original do mês.
            first = c.execute(
                "SELECT MIN(data) AS primeira FROM transactions WHERE user_id=? AND recorrencia_id=?",
                (uid, r["id"])
            ).fetchone()["primeira"]

            # CONCEITO: EXPRESSÃO CONDICIONAL E VALOR None
            # first só existe se já houve lançamento gerado. Caso contrário,
            # a própria data devida é usada como âncora.
            anchor = date.fromisoformat(first) if first else due
            occurrence_index = 0

            # CONCEITO: LAÇO WHILE
            # Avança o índice até a ocorrência correspondente à data devida.
            while _recurrence_date(anchor, r["frequencia"], occurrence_index) < due:
                occurrence_index += 1

            processed = 0
            next_due = due

            # CONCEITO: CONDIÇÃO COMPOSTA COM AND
            # O laço para quando a data passa de hoje ou o limite é atingido.
            while next_due <= today and processed < cap:
                cur = c.execute(
                    """INSERT OR IGNORE INTO transactions
                    (user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,recorrencia_id)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (uid, r["tipo"], r["descricao"], r["valor"], next_due.isoformat(),
                     r["categoria"], r["conta"],
                     "pendente" if r["tipo"] == "despesa" else None,
                     r["observacoes"], r["id"])
                )
                created += cur.rowcount
                processed += 1
                occurrence_index += 1
                next_due = _recurrence_date(anchor, r["frequencia"], occurrence_index)
            # Se atingir o limite, mantém a próxima data vencida para continuar no próximo ciclo.
            c.execute(
                "UPDATE recurring SET proxima_data=? WHERE id=? AND user_id=?",
                (next_due.isoformat(), r["id"], uid)
            )
    return created

def notifications(uid):
    """Gera notificações de contas a vencer e de orçamentos próximos do limite.

    Conceitos aplicados: listas, laços, comparação de datas, f-strings com
    formatação de data, decisão e INSERT OR IGNORE para evitar duplicidade.
    """
    today=date.today()

    # CONCEITO: timedelta E DICIONÁRIO DE FILTROS
    # A consulta busca despesas pendentes com data até sete dias à frente.
    tx=list_transactions(uid,{"tipo":"despesa","status":"pendente","fim":(today+timedelta(days=7)).isoformat()})
    with conn() as c:
        for r in tx:
            due=date.fromisoformat(r["data"])

            # CONCEITO: IF/ELSE E FORMATAÇÃO DE DATAS
            # due:%d/%m/%Y aplica a máscara brasileira dentro da f-string.
            if due<today: title="Conta vencida"; msg=f'{r["descricao"]} venceu em {due:%d/%m/%Y}.'
            else: title="Conta próxima do vencimento"; msg=f'{r["descricao"]} vence em {due:%d/%m/%Y}.'
            c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(uid,title,msg,f'tx:{r["id"]}:{r["status"]}'))

        month=today.strftime("%Y-%m")
        for b in budgets(uid,month):

            # CONCEITO: COMPARAÇÃO COM DECIMAL
            # O limite de alerta é 80% do orçamento, calculado com Decimal.
            if b["gasto"] >= b["limite_valor"] * Decimal("0.8"):
                c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(uid,"Atenção ao orçamento",f'{b["categoria"]}: {fmt(b["gasto"])} de {fmt(b["limite_valor"])}.',f'budget:{b["id"]}:{month}:{int(b["gasto"]>=b["limite_valor"])}'))
        return [dict(r) for r in c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY criada_em DESC",(uid,)).fetchall()]
def mark_notification_read(uid,nid):
    """Marca uma notificação específica como lida."""
    with conn() as c: c.execute("UPDATE notifications SET lida=1 WHERE id=? AND user_id=?",(nid,uid))

def _backup_fingerprint(payload):
    """Calcula o SHA-256 do backup, ignorando o próprio campo de integridade."""
    # CONCEITO: DICT COMPREHENSION E JSON CANÔNICO
    # A compreensão copia o dicionário sem a chave integrity_sha256. sort_keys
    # e separators fixos produzem o mesmo texto para os mesmos dados; por isso
    # o hash é estável. ensure_ascii=False preserva acentos legíveis.
    clean={k:v for k,v in payload.items() if k!="integrity_sha256"}
    canonical=json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def backup_db(uid):
    """Exporta somente os dados do usuário e inclui checksum para detectar alterações.

    Conceitos aplicados: dicionário, laço sobre tupla, compreensão de lista,
    f-string em SQL, JSON com ensure_ascii=False e retorno em bytes UTF-8.
    """
    payload={"schema_version":2,"produto":"Finaxis 2.0",
             "gerado_em":datetime.now().isoformat(timespec="seconds"),"usuario":user(uid)}
    with conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE id=?",(uid,)).fetchone():
            raise ValueError("Usuário não encontrado.")
        # CONCEITO: REPETIÇÃO SOBRE TUPLA E LIST COMPREHENSION
        # O nome da tabela é controlado por uma tupla fixa, não pela entrada
        # do usuário. A lista de dicionários representa as linhas exportadas.
        for table in ("categories","accounts","transactions","budgets","cards","card_purchases",
                      "card_invoice_payments","recurring","notifications","settings"):
            payload[table]=[dict(r) for r in c.execute(
                f"SELECT * FROM {table} WHERE user_id=?",(uid,)).fetchall()]
    payload["integrity_sha256"]=_backup_fingerprint(payload)

    # CONCEITO: SERIALIZAÇÃO JSON E CODIFICAÇÃO
    # indent=2 deixa o arquivo legível. encode("utf-8") devolve bytes, tipo
    # adequado para download.
    return json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")

def database_health(uid):
    """Verifica integridade estrutural SQLite e consistência referencial.

    Conceitos aplicados: acesso por índice, compreensão de lista, dicionário
    de contagens, comparação com None e operadores lógicos no retorno.
    """
    with conn() as c:
        # CONCEITO: ACESSO POR ÍNDICE E COMPREENSÃO
        # r[0] lê a primeira coluna de cada linha retornada pelo PRAGMA.
        integrity=[r[0] for r in c.execute("PRAGMA integrity_check").fetchall()]
        foreign_keys=[dict(r) for r in c.execute("PRAGMA foreign_key_check").fetchall()]
        counts={}
        for table in ("categories","accounts","transactions","budgets","cards",
                      "card_purchases","card_invoice_payments","recurring","notifications"):
            counts[table]=c.execute(
                f"SELECT COUNT(*) FROM {table} WHERE user_id=?",(uid,)).fetchone()[0]
        exists=c.execute("SELECT 1 FROM users WHERE id=?",(uid,)).fetchone() is not None
    return {"ok":exists and integrity==["ok"] and not foreign_keys,
            "integrity":integrity,"foreign_key_errors":foreign_keys,"counts":counts}

def restore_backup(uid, raw_json):
    """Valida e restaura um backup JSON de forma transacional e idempotente."""
    # CONCEITO: isinstance, EXPRESSÃO CONDICIONAL E BYTES
    # O conteúdo pode chegar como bytes ou texto. Se não for bytes, é
    # convertido para UTF-8. len mede o tamanho em bytes.
    raw=raw_json if isinstance(raw_json,(bytes,bytearray)) else str(raw_json).encode("utf-8")
    if len(raw)>20*1024*1024: raise ValueError("Backup excede o limite de 20 MB.")

    # CONCEITO: JSON E TRATAMENTO DE EXCEÇÃO
    try: payload=json.loads(raw.decode("utf-8"))
    except Exception: raise ValueError("O arquivo não é um JSON válido.")
    required=("categories","accounts","transactions","budgets","cards","card_purchases","recurring","notifications")
    optional=("card_invoice_payments","settings")
    if not isinstance(payload,dict) or payload.get("produto")!="Finaxis 2.0":
        raise ValueError("O arquivo não parece ser um backup Finaxis compatível.")
    if payload.get("schema_version")!=2:
        raise ValueError("Versão de backup não suportada. Importe um backup Finaxis 2.0 compatível.")
    if any(k not in payload or not isinstance(payload[k],list) for k in required):
        raise ValueError("O backup está incompleto ou contém coleções inválidas.")
    if any(k in payload and not isinstance(payload[k],list) for k in optional):
        raise ValueError("Uma coleção opcional do backup é inválida.")
    # CONCEITO: CONCATENAÇÃO DE TUPLAS E EXPRESSÃO GERADORA
    # required é tupla; a expressão geradora seleciona apenas opcionais
    # presentes e tuple(...) materializa o resultado. A soma usa len.
    collections=required+tuple(k for k in optional if k in payload)
    total=sum(len(payload[k]) for k in collections)
    if total>100000: raise ValueError("O backup excede o limite de 100.000 registros.")

    # CONCEITO: any E COMPREENSÃO/GERADOR
    # any devolve True no primeiro registro que não seja dicionário.
    for table in collections:
        if any(not isinstance(row,dict) for row in payload[table]):
            raise ValueError(f"O backup contém registros inválidos na coleção {table}.")

    # CONCEITO: COMPARAÇÃO SEGURA DE HASH
    # supplied pode ser None em backups antigos. compare_digest evita
    # diferenças de tempo na comparação.
    supplied=payload.get("integrity_sha256")
    fingerprint=_backup_fingerprint(payload)
    if supplied and (not isinstance(supplied,str) or not hmac.compare_digest(supplied,fingerprint)):
        raise ValueError("A verificação de integridade do backup falhou. O arquivo pode ter sido alterado ou corrompido.")
    for row in payload["transactions"]:
        if row.get("tipo") not in ("receita","despesa","transferencia") or not str(row.get("descricao") or "").strip():
            raise ValueError("O backup contém um lançamento sem tipo ou descrição válida.")
        try:
            money(row.get("valor",0)); date.fromisoformat(str(row.get("data") or ""))
        except (ValueError,TypeError):
            raise ValueError("O backup contém lançamento com valor ou data inválida.")
    for row in payload["accounts"]:
        if not str(row.get("nome") or "").strip(): raise ValueError("O backup contém uma conta sem nome.")
        money(row.get("saldo_inicial",0))
    for row in payload["categories"]:
        if row.get("tipo") not in TIPOS or not str(row.get("nome") or "").strip():
            raise ValueError("O backup contém categoria inválida.")
    with conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE id=?",(uid,)).fetchone(): raise ValueError("Usuário não encontrado.")
        if c.execute("SELECT 1 FROM backup_imports WHERE user_id=? AND fingerprint=?",(uid,fingerprint)).fetchone():
            return "Este backup já foi restaurado anteriormente nesta conta. Nenhum dado foi duplicado."
        for r in payload["categories"]:
            c.execute("INSERT OR IGNORE INTO categories(user_id,nome,tipo,ativo) VALUES(?,?,?,?)",
                      (uid,r["nome"],r["tipo"],int(r.get("ativo",1))))
        for r in payload["accounts"]:
            c.execute("INSERT OR IGNORE INTO accounts(user_id,nome,tipo,saldo_inicial,ativo) VALUES(?,?,?,?,?)",
                      (uid,r["nome"],r.get("tipo","Conta corrente"),money_str(r.get("saldo_inicial",0)),int(r.get("ativo",1))))
        account_names={r["nome"] for r in c.execute("SELECT nome FROM accounts WHERE user_id=?",(uid,)).fetchall()}
        tx_id_map={}
        for r in payload["transactions"]:
            account=str(r.get("conta") or "Conta principal")
            if account not in account_names:
                c.execute("INSERT OR IGNORE INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",
                          (uid,account,"Conta importada","0.00")); account_names.add(account)
            cur=c.execute("""INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id,parcela_atual,parcelas_total)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
              (uid,r["tipo"],r["descricao"],money_str(r.get("valor",0)),date.fromisoformat(str(r["data"])).isoformat(),
               r.get("categoria","Outros"),account,r.get("status"),r.get("observacoes",""),
               r.get("transferencia_id"),r.get("parcela_atual"),r.get("parcelas_total")))
            if r.get("id") is not None: tx_id_map[str(r["id"])]=cur.lastrowid
        for r in payload["budgets"]:
            c.execute("""INSERT INTO budgets(user_id,categoria,mes,limite) VALUES(?,?,?,?)
              ON CONFLICT(user_id,categoria,mes) DO UPDATE SET limite=excluded.limite""",
              (uid,r.get("categoria","Outros"),r.get("mes",date.today().strftime("%Y-%m")),money_str(r.get("limite",0))))
        for r in payload["cards"]:
            c.execute("INSERT OR IGNORE INTO cards(user_id,nome,limite,fechamento,vencimento,ativo) VALUES(?,?,?,?,?,?)",
                      (uid,r.get("nome","Cartão importado"),money_str(r.get("limite",0)),int(r.get("fechamento",20)),int(r.get("vencimento",5)),int(r.get("ativo",1))))
        card_map={r["nome"]:r["id"] for r in c.execute("SELECT id,nome FROM cards WHERE user_id=?",(uid,)).fetchall()}
        for r in payload["card_purchases"]:
            card_name=r.get("cartao") or next((x.get("nome") for x in payload["cards"] if x.get("id")==r.get("card_id")),None)
            card_id=card_map.get(card_name)
            if card_id:
                c.execute("INSERT INTO card_purchases(user_id,card_id,descricao,valor_total,data,categoria,parcelas) VALUES(?,?,?,?,?,?,?)",
                          (uid,card_id,r.get("descricao","Compra importada"),money_str(r.get("valor_total",0)),str(r.get("data") or date.today().isoformat())[:10],r.get("categoria","Outros"),max(1,min(60,int(r.get("parcelas",1))))))
        for r in payload.get("card_invoice_payments",[]):
            card_name=r.get("cartao") or next((x.get("nome") for x in payload["cards"] if x.get("id")==r.get("card_id")),None)
            card_id=card_map.get(card_name); txid=tx_id_map.get(str(r.get("transaction_id")))
            if card_id and txid:
                c.execute("INSERT INTO card_invoice_payments(user_id,card_id,mes_ref,valor,data_pagamento,conta,transaction_id,observacoes) VALUES(?,?,?,?,?,?,?,?)",
                          (uid,card_id,r.get("mes_ref",date.today().strftime("%Y-%m")),money_str(r.get("valor",0)),str(r.get("data_pagamento") or date.today().isoformat())[:10],r.get("conta","Conta principal"),txid,r.get("observacoes","")))
        for r in payload["recurring"]:
            c.execute("INSERT INTO recurring(user_id,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,ativo,observacoes) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (uid,r.get("tipo","despesa"),r.get("descricao","Recorrência importada"),money_str(r.get("valor",0)),r.get("categoria","Outros"),r.get("conta","Conta principal"),r.get("frequencia","Mensal"),str(r.get("proxima_data") or date.today().isoformat())[:10],int(r.get("ativo",1)),r.get("observacoes","")))
        for r in payload["notifications"]:
            c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave,lida) VALUES(?,?,?,?,?)",
                      (uid,r.get("titulo","Notificação importada"),r.get("mensagem",""),"restore:"+str(r.get("chave",secrets.token_hex(8))),int(r.get("lida",0))))
        for r in payload.get("settings",[]):
            c.execute("UPDATE settings SET tema=?,moeda=?,nome_exibicao=? WHERE user_id=?",
                      (r.get("tema","Claro"),r.get("moeda","BRL"),r.get("nome_exibicao"),uid))
        c.execute("INSERT INTO backup_imports(user_id,fingerprint) VALUES(?,?)",(uid,fingerprint))
    audit_event(uid,"backup_restaurado",f"Importação de backup {fingerprint[:12]}")
    return f"Backup importado e restaurado com sucesso ({total} registros analisados). A importação é registrada para impedir repetir o mesmo arquivo."

def migrate_legacy(uid, legacy_path=None):
    """Migra categorias e lançamentos da V1 sem escrever na base de origem.

    Conceitos aplicados: Path, existência de arquivo, conexão SQLite somente
    leitura (mode=ro), conjuntos de tabelas, dicionários, laços, validação de
    datas e try/except/finally. O finally fecha a conexão antiga mesmo em erro.
    """
    path=Path(legacy_path or LEGACY_DB)
    if not path.exists(): return {"ok":False,"message":f"Banco antigo não encontrado em {path}."}
    with conn() as c:
        u=c.execute("SELECT data_migracao_v1 FROM users WHERE id=?",(uid,)).fetchone()
        if not u: return {"ok":False,"message":"Usuário inexistente."}
        if u["data_migracao_v1"]: return {"ok":False,"message":"A migração já foi executada para este usuário."}
    # CONCEITO: PATH, URI E CONEXÃO SOMENTE LEITURA
    # as_uri converte o caminho em URI. O parâmetro mode=ro impede que a
    # migração altere o banco antigo.
    old=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True); old.row_factory=sqlite3.Row
    try:
        # CONCEITO: SET COMPREHENSION
        # O conjunto contém os nomes das tabelas existentes na base antiga.
        old_tables={r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "transactions" not in old_tables or "categories" not in old_tables:
            return {"ok":False,"message":"Estrutura da V1 não reconhecida: eram esperadas as tabelas transactions e categories."}
        old_tx=[dict(r) for r in old.execute("SELECT * FROM transactions ORDER BY id")]
        old_cats=[dict(r) for r in old.execute("SELECT * FROM categories ORDER BY id")]
        imported=0; imported_categories=0
        with conn() as c:
            for cat in old_cats:
                tipo=cat.get("tipo","despesa")
                if tipo not in TIPOS: continue
                nome=str(cat.get("nome") or "Outros").strip()
                before=c.total_changes
                c.execute("INSERT OR IGNORE INTO categories(user_id,nome,tipo) VALUES(?,?,?)",(uid,nome,tipo))
                imported_categories += c.total_changes-before
            for r in old_tx:
                tipo=str(r.get("tipo") or "").lower()
                if tipo not in TIPOS: continue
                desc=str(r.get("descricao") or "Lançamento importado").strip()
                val=money_str(r.get("valor") or 0)
                if money(val)<=0: continue
                dt=str(r.get("data") or date.today().isoformat())[:10]
                try: dt=date.fromisoformat(dt).isoformat()
                except ValueError: raise ValueError(f"Data inválida no lançamento legado ID {r.get('id')}.")
                cat=str(r.get("categoria") or "Outros").strip()
                conta=str(r.get("conta") or "Conta principal").strip()
                status=str(r.get("status") or "").lower() if tipo=="despesa" else None
                if tipo=="despesa" and status not in STATUS: status="pendente"
                obs=str(r.get("observacoes") or "")
                c.execute("INSERT OR IGNORE INTO categories(user_id,nome,tipo) VALUES(?,?,?)",(uid,cat,tipo))
                c.execute("INSERT OR IGNORE INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",(uid,conta,"Conta importada","0.00"))
                c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes) VALUES(?,?,?,?,?,?,?,?,?)",
                          (uid,tipo,desc,val,dt,cat,conta,status,obs))
                imported+=1
            c.execute("UPDATE users SET data_migracao_v1=? WHERE id=?",(datetime.now().isoformat(timespec="seconds"),uid))
        return {"ok":True,"message":f"Migração concluída: {imported} lançamentos e {imported_categories} categorias novas importadas. Base original aberta somente para leitura."}
    # CONCEITO: TRATAMENTO DE EXCEÇÃO E FINALLY
    # O except devolve um dicionário de erro em vez de encerrar o programa.
    # O finally fecha a conexão antiga independentemente de sucesso ou falha.
    except Exception as e:
        return {"ok":False,"message":f"Falha na migração; as alterações da migração foram revertidas: {e}"}
    finally: old.close()
