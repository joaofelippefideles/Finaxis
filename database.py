from __future__ import annotations
import os, sqlite3, hashlib, hmac, secrets, shutil, json, csv
from pathlib import Path
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FINAXIS_DB", BASE_DIR / "data" / "finaxis_v2.db"))
LEGACY_DB = Path(os.environ.get("FINAXIS_V1_DB", BASE_DIR / "data" / "financeiro_v1.db"))
TIPOS = ("receita", "despesa")
STATUS = ("pendente", "pago")

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 moeda TEXT NOT NULL DEFAULT 'BRL', data_migracao_v1 TEXT
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
"""

DEFAULT_CATEGORIES = [
 ("Salário","receita"),("Freelance","receita"),("Investimentos","receita"),("Outros","receita"),
 ("Moradia","despesa"),("Alimentação","despesa"),("Transporte","despesa"),("Saúde","despesa"),
 ("Educação","despesa"),("Lazer","despesa"),("Contas","despesa"),("Outros","despesa")
]
def money(v):
    """Converte valores em Decimal; aceita números e formatos brasileiros como R$ 1.234,56."""
    raw = str(v).strip().replace("R$", "").replace(" ", "") if isinstance(v, str) else str(v)
    if isinstance(v, str) and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        d = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor monetário válido.")
    if not d.is_finite():
        raise ValueError("Valor inválido.")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def money_str(v): return format(money(v), ".2f")
def fmt(v): return "R$ " + f"{money(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
@contextmanager
def conn():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB_PATH,timeout=15)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=15000")
    try:
        yield c; c.commit()
    except Exception:
        c.rollback(); raise
    finally: c.close()
def init_db():
    with conn() as c:
        c.executescript(SCHEMA)
def hash_password(password, salt=None):
    if len(password)<10: raise ValueError("A senha deve ter pelo menos 10 caracteres.")
    salt=salt or secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return salt.hex()+":"+digest.hex()
def verify_password(password, encoded):
    try:
        salt_hex,digest_hex=encoded.split(":")
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),310000).hex()
        return hmac.compare_digest(actual,digest_hex)
    except Exception: return False
def create_user(nome,email,password):
    nome=nome.strip(); email=email.strip().lower()
    if not nome: raise ValueError("Informe seu nome.")
    if "@" not in email or "." not in email.split("@")[-1]: raise ValueError("Informe um e-mail válido.")
    ph=hash_password(password)
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
    key=(email or "").strip().lower()
    with conn() as c:
        row=c.execute("SELECT locked_until FROM login_attempts WHERE email=?",(key,)).fetchone()
    if not row or not row["locked_until"]: return False
    try: return datetime.fromisoformat(row["locked_until"]) > datetime.now()
    except ValueError: return False

def register_login_failure(email, max_failures=5, lock_minutes=15):
    key=(email or "").strip().lower()
    now=datetime.now()
    with conn() as c:
        row=c.execute("SELECT failures FROM login_attempts WHERE email=?",(key,)).fetchone()
        failures=(row["failures"] if row else 0)+1
        locked=(now+timedelta(minutes=lock_minutes)).isoformat(timespec="seconds") if failures>=max_failures else None
        c.execute("INSERT INTO login_attempts(email,failures,locked_until,updated_at) VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until,updated_at=excluded.updated_at",(key,failures,locked,now.isoformat(timespec="seconds")))
    return failures, bool(locked)

def clear_login_failures(email):
    with conn() as c: c.execute("DELETE FROM login_attempts WHERE email=?",((email or "").strip().lower(),))

def authenticate(email,password):
    key=(email or "").strip().lower()
    if login_locked(key): return None
    with conn() as c: row=c.execute("SELECT * FROM users WHERE email=?",(key,)).fetchone()
    if row and verify_password(password,row["password_hash"]):
        clear_login_failures(key)
        return dict(row)
    register_login_failure(key)
    return None

def audit_event(uid, evento, detalhe=""):
    with conn() as c: c.execute("INSERT INTO audit_log(user_id,evento,detalhe) VALUES(?,?,?)",(uid,evento,str(detalhe)[:500]))

def audit_events(uid, limit=100):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT evento,detalhe,criado_em FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT ?",(uid,max(1,min(int(limit),500)))).fetchall()]

def mark_all_notifications_read(uid):
    with conn() as c: return c.execute("UPDATE notifications SET lida=1 WHERE user_id=? AND lida=0",(uid,)).rowcount
def user(uid):
    with conn() as c: r=c.execute("SELECT id,nome,email,moeda,data_migracao_v1 FROM users WHERE id=?",(uid,)).fetchone()
    return dict(r) if r else None
def update_profile(uid,nome,moeda):
    if not nome.strip(): raise ValueError("Informe o nome.")
    with conn() as c:
        c.execute("UPDATE users SET nome=?,moeda=? WHERE id=?",(nome.strip(),moeda,uid))
        c.execute("UPDATE settings SET nome_exibicao=?,moeda=? WHERE user_id=?",(nome.strip(),moeda,uid))
def categories(uid,tipo=None):
    with conn() as c:
        if tipo: rows=c.execute("SELECT * FROM categories WHERE user_id=? AND tipo=? AND ativo=1 ORDER BY nome",(uid,tipo)).fetchall()
        else: rows=c.execute("SELECT * FROM categories WHERE user_id=? ORDER BY tipo,nome",(uid,)).fetchall()
    return [dict(r) for r in rows]
def add_category(uid,nome,tipo):
    if tipo not in TIPOS or not nome.strip(): raise ValueError("Informe nome e tipo válidos.")
    with conn() as c:
        try: c.execute("INSERT INTO categories(user_id,nome,tipo) VALUES(?,?,?)",(uid,nome.strip(),tipo))
        except sqlite3.IntegrityError: raise ValueError("Categoria já existe.")
def rename_category(uid,cid,nome):
    with conn() as c:
        row=c.execute("SELECT nome,tipo FROM categories WHERE id=? AND user_id=?",(cid,uid)).fetchone()
        if not row: raise ValueError("Categoria não encontrada.")
        try:
            c.execute("UPDATE categories SET nome=? WHERE id=? AND user_id=?",(nome.strip(),cid,uid))
            c.execute("UPDATE transactions SET categoria=? WHERE user_id=? AND categoria=?",(nome.strip(),uid,row["nome"]))
            c.execute("UPDATE budgets SET categoria=? WHERE user_id=? AND categoria=?",(nome.strip(),uid,row["nome"]))
        except sqlite3.IntegrityError: raise ValueError("Já existe uma categoria com esse nome.")

def toggle_category(uid,cid,active):
    with conn() as c:
        cur=c.execute("UPDATE categories SET ativo=? WHERE id=? AND user_id=?",(1 if active else 0,cid,uid))
        if cur.rowcount==0: raise ValueError("Categoria não encontrada.")
def save_theme(uid,tema):
    if tema not in ("Claro","Escuro"): raise ValueError("Tema inválido.")
    with conn() as c: c.execute("UPDATE settings SET tema=? WHERE user_id=?",(tema,uid))
def get_theme(uid):
    with conn() as c:
        row=c.execute("SELECT tema FROM settings WHERE user_id=?",(uid,)).fetchone()
    return row["tema"] if row else "Claro"

def add_account(uid,nome,tipo,saldo):
    if not nome.strip(): raise ValueError("Informe o nome da conta.")
    with conn() as c:
        try: c.execute("INSERT INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",(uid,nome.strip(),tipo,money_str(saldo)))
        except sqlite3.IntegrityError: raise ValueError("Já existe uma conta com esse nome.")
def accounts(uid):
    """Saldo atual: saldo inicial + receitas - despesas pagas +/- transferências."""
    with conn() as c:
        rows=c.execute("SELECT * FROM accounts WHERE user_id=? AND ativo=1 ORDER BY nome",(uid,)).fetchall()
        tx_rows=c.execute("SELECT conta,tipo,valor,status FROM transactions WHERE user_id=?",(uid,)).fetchall()
    by_account={}
    for t in tx_rows:
        by_account.setdefault(t["conta"], []).append(t)
    result=[]
    for r in rows:
        d=dict(r); d["saldo"]=money(d["saldo_inicial"])
        for t in by_account.get(d["nome"], []):
            v=money(t["valor"])
            if t["tipo"]=="receita": d["saldo"] += v
            elif t["tipo"]=="despesa" and t["status"]=="pago": d["saldo"] -= v
            elif t["tipo"]=="transferencia":
                if (t["status"] or "") == "entrada": d["saldo"] += v
                elif (t["status"] or "") == "saida": d["saldo"] -= v
        result.append(d)
    return result
def add_transaction(uid,tipo,descricao,valor,data_lancamento,categoria,conta,status=None,observacoes="", transferencia_id=None, parcela_atual=None, parcelas_total=None):
    if tipo not in ("receita","despesa","transferencia"): raise ValueError("Tipo inválido.")
    if not descricao.strip() or not categoria.strip() or not conta.strip(): raise ValueError("Preencha descrição, categoria e conta.")
    valor=money(valor)
    if valor<=0: raise ValueError("O valor deve ser maior que zero.")
    try: d=date.fromisoformat(str(data_lancamento)).isoformat()
    except ValueError: raise ValueError("Data inválida.")
    if tipo=="despesa": status=status if status in STATUS else "pendente"
    elif tipo=="transferencia": status=status if status in ("entrada","saida") else None
    else: status=None
    with conn() as c:
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone(): raise ValueError("Conta não encontrada.")
        if tipo in TIPOS and not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo=? AND ativo=1",(uid,categoria,tipo)).fetchone():
            raise ValueError("Categoria inválida para este tipo.")
        cur=c.execute("""INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id,parcela_atual,parcelas_total)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(uid,tipo,descricao.strip(),str(valor),d,categoria,conta,status,observacoes.strip(),transferencia_id,parcela_atual,parcelas_total))
        return cur.lastrowid
def list_transactions(uid, filtros=None):
    filtros=filtros or {}; sql="SELECT * FROM transactions WHERE user_id=?"; p=[uid]
    for key, col in [("tipo","tipo"),("categoria","categoria"),("conta","conta"),("status","status")]:
        v=filtros.get(key)
        if v and v!="Todos": sql+=f" AND {col}=?"; p.append(v)
    if filtros.get("inicio"): sql+=" AND data>=?"; p.append(str(filtros["inicio"]))
    if filtros.get("fim"): sql+=" AND data<=?"; p.append(str(filtros["fim"]))
    if filtros.get("busca"): sql+=" AND (descricao LIKE ? OR observacoes LIKE ?)"; p.extend([f"%{filtros['busca']}%",f"%{filtros['busca']}%"])
    sql+=" ORDER BY data DESC,id DESC"
    with conn() as c: return [dict(r) for r in c.execute(sql,p).fetchall()]
def delete_transaction(uid,tid):
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
    rows=list_transactions(uid,{"inicio":inicio,"fim":fim})
    rec=sum((money(r["valor"]) for r in rows if r["tipo"]=="receita"),money(0))
    desp=sum((money(r["valor"]) for r in rows if r["tipo"]=="despesa" and r["status"]=="pago"),money(0))
    pend=sum((money(r["valor"]) for r in rows if r["tipo"]=="despesa" and r["status"]=="pendente"),money(0))
    return {"receitas":rec,"despesas_pagas":desp,"pendentes":pend,"saldo":rec-desp}
def add_budget(uid,categoria,mes,limite):
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
    with conn() as c:
        rows=c.execute("SELECT * FROM budgets WHERE user_id=? AND mes=? ORDER BY categoria",(uid,mes)).fetchall()
        tx=c.execute("SELECT categoria,valor FROM transactions WHERE user_id=? AND tipo='despesa' AND status='pago' AND substr(data,1,7)=?",(uid,mes)).fetchall()
    spent_by_category={}
    for t in tx: spent_by_category[t["categoria"]]=spent_by_category.get(t["categoria"],money(0))+money(t["valor"])
    out=[]
    for r in rows:
        d=dict(r); d["gasto"]=spent_by_category.get(d["categoria"],money(0)); d["limite_valor"]=money(d["limite"]); out.append(d)
    return out
def add_card(uid,nome,limite,fechamento,vencimento):
    nome=(nome or "").strip(); limite=money(limite)
    if not nome or limite<=0 or not 1<=int(fechamento)<=28 or not 1<=int(vencimento)<=28:
        raise ValueError("Informe nome, limite positivo e dias válidos (1 a 28).")
    with conn() as c:
        try: c.execute("INSERT INTO cards(user_id,nome,limite,fechamento,vencimento) VALUES(?,?,?,?,?)",(uid,nome,str(limite),int(fechamento),int(vencimento)))
        except sqlite3.IntegrityError: raise ValueError("Cartão já cadastrado.")
def cards(uid):
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM cards WHERE user_id=? AND ativo=1 ORDER BY nome",(uid,)).fetchall()]
def add_purchase(uid,card_id,descricao,valor,data_lancamento,categoria,parcelas):
    valor=money(valor); parcelas=int(parcelas); descricao=(descricao or "").strip()
    if not descricao: raise ValueError("Informe a descrição da compra.")
    if valor<=0 or parcelas<1 or parcelas>60: raise ValueError("Valor ou número de parcelas inválido.")
    dt=date.fromisoformat(str(data_lancamento)).isoformat()
    with conn() as c:
        if not c.execute("SELECT 1 FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone(): raise ValueError("Cartão inválido.")
        if not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo='despesa' AND ativo=1",(uid,categoria)).fetchone(): raise ValueError("Categoria de despesa inválida.")
        c.execute("INSERT INTO card_purchases(user_id,card_id,descricao,valor_total,data,categoria,parcelas) VALUES(?,?,?,?,?,?,?)",(uid,card_id,descricao,str(valor),dt,categoria,parcelas))
def purchases(uid):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT p.*,c.nome cartao,c.limite,c.fechamento,c.vencimento FROM card_purchases p JOIN cards c ON c.id=p.card_id WHERE p.user_id=? ORDER BY p.data DESC",(uid,)).fetchall()]
def _add_month(year, month, offset=1):
    index=year*12+(month-1)+offset
    return index//12, index%12+1
def _invoice_month(purchase_date, closing_day):
    d=date.fromisoformat(str(purchase_date)); y,m=d.year,d.month
    if d.day>int(closing_day): y,m=_add_month(y,m,1)
    return y,m
def _installment_values(total, count):
    cents=int(money(total)*100); base,extra=divmod(cents,count)
    return [Decimal(base+(1 if i<extra else 0))/Decimal(100) for i in range(count)]
def card_invoice(uid, card_id, mes_ref):
    """Calcula fatura do mês de fechamento e o vencimento no mês seguinte."""
    try: year,month=map(int,mes_ref.split("-")); date(year,month,1)
    except Exception: raise ValueError("Mês da fatura inválido; use AAAA-MM.")
    with conn() as c:
        card=c.execute("SELECT * FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone()
        if not card: raise ValueError("Cartão não encontrado.")
        rows=c.execute("SELECT * FROM card_purchases WHERE user_id=? AND card_id=?",(uid,card_id)).fetchall()
        payments=c.execute("SELECT valor FROM card_invoice_payments WHERE user_id=? AND card_id=? AND mes_ref=?",(uid,card_id,mes_ref)).fetchall()
    lines=[]; total=money(0)
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
    import calendar
    due_day=min(int(card["vencimento"]),calendar.monthrange(due_year,due_month)[1])
    return {"cartao":card["nome"],"card_id":card_id,"mes_ref":mes_ref,"vencimento":date(due_year,due_month,due_day).isoformat(),"itens":lines,"total":total,"pago":paid,"aberto":max(money(0),total-paid),"limite":money(card["limite"])}
def pay_card_invoice(uid, card_id, mes_ref, valor, conta, data_pagamento=None, observacoes=""):
    """Baixa uma fatura e registra a saída na conta escolhida, numa única transação."""
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
    with conn() as c:
        card=c.execute("SELECT fechamento FROM cards WHERE id=? AND user_id=? AND ativo=1",(card_id,uid)).fetchone()
        rows=c.execute("SELECT data,parcelas,valor_total FROM card_purchases WHERE user_id=? AND card_id=?",(uid,card_id)).fetchall()
    if not card: raise ValueError("Cartão não encontrado.")
    months=set()
    for purchase in rows:
        y,m=_invoice_month(purchase["data"],card["fechamento"])
        for offset in range(int(purchase["parcelas"])):
            yy,mm=_add_month(y,m,offset); months.add(f"{yy:04d}-{mm:02d}")
    current=date.today().strftime("%Y-%m")
    return sum((card_invoice(uid,card_id,month)["aberto"] for month in sorted(months) if month>=current),money(0))
def add_transfer(uid,descricao,valor,data_lancamento,origem,destino):
    """Registra as duas pontas de uma transferência atomicamente."""
    descricao=(descricao or "").strip(); value=money(valor); dt=date.fromisoformat(str(data_lancamento)).isoformat()
    if not descricao: raise ValueError("Informe a descrição da transferência.")
    if value<=0: raise ValueError("O valor deve ser maior que zero.")
    if origem==destino: raise ValueError("Origem e destino devem ser diferentes.")
    transfer_id=secrets.token_hex(16)
    with conn() as c:
        for account in (origem,destino):
            if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,account)).fetchone(): raise ValueError(f"Conta não encontrada: {account}.")
        c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,"transferencia",descricao,str(value),dt,"Transferência",origem,"saida","Saída da transferência",transfer_id))
        c.execute("INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,"transferencia",descricao,str(value),dt,"Transferência",destino,"entrada","Entrada da transferência",transfer_id))
    return transfer_id

def add_recurring(uid,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,observacoes=""):
    if tipo not in TIPOS or frequencia not in ("Diária","Semanal","Mensal","Anual"): raise ValueError("Tipo ou frequência inválida.")
    dt=date.fromisoformat(str(proxima_data)).isoformat(); valor=money(valor); descricao=(descricao or "").strip()
    if not descricao: raise ValueError("Informe a descrição da recorrência.")
    if valor<=0: raise ValueError("Valor deve ser positivo.")
    with conn() as c:
        if not c.execute("SELECT 1 FROM accounts WHERE user_id=? AND nome=? AND ativo=1",(uid,conta)).fetchone(): raise ValueError("Conta não encontrada.")
        if not c.execute("SELECT 1 FROM categories WHERE user_id=? AND nome=? AND tipo=? AND ativo=1",(uid,categoria,tipo)).fetchone(): raise ValueError("Categoria inválida para o tipo escolhido.")
        c.execute("INSERT INTO recurring(user_id,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,observacoes) VALUES(?,?,?,?,?,?,?,?,?)",(uid,tipo,descricao,str(valor),categoria,conta,frequencia,dt,(observacoes or "").strip()))
def recurrings(uid):
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM recurring WHERE user_id=? ORDER BY proxima_data",(uid,)).fetchall()]
def run_recurring(uid):
    """Gera ocorrências vencidas uma única vez; datas mensais/anuais tratam finais de mês e ano bissexto."""
    today=date.today(); created=0
    import calendar
    with conn() as c:
        rows=c.execute("SELECT * FROM recurring WHERE user_id=? AND ativo=1 AND proxima_data<=?",(uid,today.isoformat())).fetchall()
        for r in rows:
            d=date.fromisoformat(r["proxima_data"])
            while d<=today:
                cur=c.execute("INSERT OR IGNORE INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,recorrencia_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (uid,r["tipo"],r["descricao"],r["valor"],d.isoformat(),r["categoria"],r["conta"],"pendente" if r["tipo"]=="despesa" else None,r["observacoes"],r["id"]))
                created+=cur.rowcount
                if r["frequencia"]=="Diária": d+=timedelta(days=1)
                elif r["frequencia"]=="Semanal": d+=timedelta(days=7)
                elif r["frequencia"]=="Anual":
                    try: d=d.replace(year=d.year+1)
                    except ValueError: d=d.replace(year=d.year+1,day=28)
                else:
                    y,m=_add_month(d.year,d.month,1)
                    d=d.replace(year=y,month=m,day=min(d.day,calendar.monthrange(y,m)[1]))
            c.execute("UPDATE recurring SET proxima_data=? WHERE id=? AND user_id=?",(d.isoformat(),r["id"],uid))
    return created
def notifications(uid):
    today=date.today()
    tx=list_transactions(uid,{"tipo":"despesa","status":"pendente","fim":(today+timedelta(days=7)).isoformat()})
    with conn() as c:
        for r in tx:
            due=date.fromisoformat(r["data"])
            if due<today: title="Conta vencida"; msg=f'{r["descricao"]} venceu em {due:%d/%m/%Y}.'
            else: title="Conta próxima do vencimento"; msg=f'{r["descricao"]} vence em {due:%d/%m/%Y}.'
            c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(uid,title,msg,f'tx:{r["id"]}:{r["status"]}'))
        month=today.strftime("%Y-%m")
        for b in budgets(uid,month):
            if b["gasto"]>=b["limite_valor"]*.8:
                c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(uid,"Atenção ao orçamento",f'{b["categoria"]}: {fmt(b["gasto"])} de {fmt(b["limite_valor"])}.',f'budget:{b["id"]}:{month}:{int(b["gasto"]>=b["limite_valor"])}'))
        return [dict(r) for r in c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY criada_em DESC",(uid,)).fetchall()]
def mark_notification_read(uid,nid):
    with conn() as c: c.execute("UPDATE notifications SET lida=1 WHERE id=? AND user_id=?",(nid,uid))
def backup_db(uid):
    # Exporta apenas os dados do usuário autenticado, não a base global com outros usuários.
    payload={"schema_version":2,"produto":"Finaxis 2.0","gerado_em":datetime.now().isoformat(timespec="seconds"),"usuario":user(uid)}
    with conn() as c:
        for table in ("categories","accounts","transactions","budgets","cards","card_purchases","card_invoice_payments","recurring","notifications","settings"):
            payload[table]=[dict(r) for r in c.execute(f"SELECT * FROM {table} WHERE user_id=?",(uid,)).fetchall()]
    return json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")

def restore_backup(uid, raw_json):
    try:
        payload=json.loads(raw_json.decode("utf-8") if isinstance(raw_json,(bytes,bytearray)) else raw_json)
    except Exception: raise ValueError("O arquivo não é um JSON válido.")
    if len(raw_json if isinstance(raw_json,(bytes,bytearray)) else str(raw_json).encode("utf-8")) > 20*1024*1024:
        raise ValueError("Backup excede o limite de 20 MB.")
    required=("categories","accounts","transactions","budgets","cards","card_purchases","recurring","notifications")
    if not isinstance(payload,dict) or payload.get("produto") not in (None,"Finaxis 2.0") or any(k not in payload or not isinstance(payload[k],list) for k in required):
        raise ValueError("O arquivo não parece ser um backup Finaxis compatível.")
    with conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE id=?",(uid,)).fetchone(): raise ValueError("Usuário não encontrado.")
        # Recria entidades por nome para não reutilizar IDs globais de outra conta.
        for r in payload["categories"]:
            if r.get("tipo") in TIPOS and r.get("nome"):
                c.execute("INSERT OR IGNORE INTO categories(user_id,nome,tipo,ativo) VALUES(?,?,?,?)",(uid,r["nome"],r["tipo"],int(r.get("ativo",1))))
        for r in payload["accounts"]:
            c.execute("INSERT OR IGNORE INTO accounts(user_id,nome,tipo,saldo_inicial,ativo) VALUES(?,?,?,?,?)",(uid,r.get("nome","Conta importada"),r.get("tipo","Conta corrente"),money_str(r.get("saldo_inicial",0)),int(r.get("ativo",1))))
        account_names={r["nome"] for r in c.execute("SELECT nome FROM accounts WHERE user_id=?",(uid,)).fetchall()}
        tx_id_map={}
        for r in payload["transactions"]:
            if r.get("tipo") not in ("receita","despesa","transferencia") or not r.get("descricao"): continue
            account=str(r.get("conta") or "Conta principal")
            if account not in account_names:
                c.execute("INSERT OR IGNORE INTO accounts(user_id,nome,tipo,saldo_inicial) VALUES(?,?,?,?)",(uid,account,"Conta importada","0.00"))
                account_names.add(account)
            cur=c.execute("""INSERT INTO transactions(user_id,tipo,descricao,valor,data,categoria,conta,status,observacoes,transferencia_id,parcela_atual,parcelas_total)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(uid,r["tipo"],r["descricao"],money_str(r.get("valor",0)),str(r.get("data") or date.today().isoformat())[:10],r.get("categoria","Outros"),account,r.get("status"),r.get("observacoes",""),r.get("transferencia_id"),r.get("parcela_atual"),r.get("parcelas_total")))
            if r.get("id") is not None: tx_id_map[str(r.get("id"))]=cur.lastrowid
        for r in payload["budgets"]:
            c.execute("""INSERT INTO budgets(user_id,categoria,mes,limite) VALUES(?,?,?,?)
              ON CONFLICT(user_id,categoria,mes) DO UPDATE SET limite=excluded.limite""",(uid,r.get("categoria","Outros"),r.get("mes",date.today().strftime("%Y-%m")),money_str(r.get("limite",0))))
        for r in payload["cards"]:
            c.execute("INSERT OR IGNORE INTO cards(user_id,nome,limite,fechamento,vencimento,ativo) VALUES(?,?,?,?,?,?)",(uid,r.get("nome","Cartão importado"),money_str(r.get("limite",0)),int(r.get("fechamento",20)),int(r.get("vencimento",5)),int(r.get("ativo",1))))
        card_map={r["nome"]:r["id"] for r in c.execute("SELECT id,nome FROM cards WHERE user_id=?",(uid,)).fetchall()}
        for r in payload["card_purchases"]:
            card_name=r.get("cartao")
            if not card_name and r.get("card_id"):
                card_name=next((x.get("nome") for x in payload["cards"] if x.get("id")==r.get("card_id")),None)
            card_id=card_map.get(card_name)
            if card_id:
                c.execute("INSERT INTO card_purchases(user_id,card_id,descricao,valor_total,data,categoria,parcelas) VALUES(?,?,?,?,?,?,?)",(uid,card_id,r.get("descricao","Compra importada"),money_str(r.get("valor_total",0)),str(r.get("data") or date.today().isoformat())[:10],r.get("categoria","Outros"),max(1,min(60,int(r.get("parcelas",1))))))
        for r in payload.get("card_invoice_payments",[]):
            card_name=r.get("cartao")
            if not card_name and r.get("card_id"):
                card_name=next((x.get("nome") for x in payload["cards"] if x.get("id")==r.get("card_id")),None)
            card_id=card_map.get(card_name)
            txid=tx_id_map.get(str(r.get("transaction_id")))
            if card_id and txid:
                c.execute("INSERT INTO card_invoice_payments(user_id,card_id,mes_ref,valor,data_pagamento,conta,transaction_id,observacoes) VALUES(?,?,?,?,?,?,?,?)",(uid,card_id,r.get("mes_ref",date.today().strftime("%Y-%m")),money_str(r.get("valor",0)),str(r.get("data_pagamento") or date.today().isoformat())[:10],r.get("conta","Conta principal"),txid,r.get("observacoes","")))
        for r in payload["recurring"]:
            c.execute("INSERT INTO recurring(user_id,tipo,descricao,valor,categoria,conta,frequencia,proxima_data,ativo,observacoes) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,r.get("tipo","despesa"),r.get("descricao","Recorrência importada"),money_str(r.get("valor",0)),r.get("categoria","Outros"),r.get("conta","Conta principal"),r.get("frequencia","Mensal"),str(r.get("proxima_data") or date.today().isoformat())[:10],int(r.get("ativo",1)),r.get("observacoes","")))
        for r in payload["notifications"]:
            c.execute("INSERT OR IGNORE INTO notifications(user_id,titulo,mensagem,chave,lida) VALUES(?,?,?,?,?)",(uid,r.get("titulo","Notificação importada"),r.get("mensagem",""),"restore:"+str(r.get("chave",secrets.token_hex(8))),int(r.get("lida",0))))
    audit_event(uid,"backup_restaurado","Importação de backup JSON")
    return "Backup importado. Contas e categorias foram conciliadas por nome; lançamentos foram adicionados. Verifique se não há duplicidades."

def migrate_legacy(uid, legacy_path=None):
    """Migra categorias e lançamentos da V1 sem escrever na base de origem."""
    path=Path(legacy_path or LEGACY_DB)
    if not path.exists(): return {"ok":False,"message":f"Banco antigo não encontrado em {path}."}
    with conn() as c:
        u=c.execute("SELECT data_migracao_v1 FROM users WHERE id=?",(uid,)).fetchone()
        if not u: return {"ok":False,"message":"Usuário inexistente."}
        if u["data_migracao_v1"]: return {"ok":False,"message":"A migração já foi executada para este usuário."}
    old=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True); old.row_factory=sqlite3.Row
    try:
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
    except Exception as e:
        return {"ok":False,"message":f"Falha na migração; as alterações da migração foram revertidas: {e}"}
    finally: old.close()
