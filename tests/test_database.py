import sqlite3
import tempfile
import unittest
from pathlib import Path
import database as db

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_path=db.DB_PATH
        self.old_legacy=db.LEGACY_DB
        db.DB_PATH=Path(self.tmp.name)/"test.db"
        db.LEGACY_DB=Path(self.tmp.name)/"legacy.db"
        db.init_db()
        self.uid=db.create_user("Teste","teste@example.com","senha-forte-123")
    def tearDown(self):
        db.DB_PATH=self.old_path
        db.LEGACY_DB=self.old_legacy
        self.tmp.cleanup()
    def test_password_and_isolation(self):
        self.assertIsNotNone(db.authenticate("teste@example.com","senha-forte-123"))
        other=db.create_user("Outro","outro@example.com","senha-forte-456")
        acc=db.accounts(self.uid)[0]["nome"]
        cat=db.categories(self.uid,"receita")[0]["nome"]
        db.add_transaction(self.uid,"receita","Salário",1000,"2026-01-10",cat,acc)
        self.assertEqual(len(db.list_transactions(self.uid)),1)
        self.assertEqual(len(db.list_transactions(other)),0)
    def test_transfer_atomic_balances(self):
        names=[a["nome"] for a in db.accounts(self.uid)]
        db.add_transfer(self.uid,"Transferência",50,"2026-01-10",names[0],names[1])
        balances={a["nome"]:a["saldo"] for a in db.accounts(self.uid)}
        self.assertEqual(balances[names[0]],db.money(-50))
        self.assertEqual(balances[names[1]],db.money(50))
        rows=db.list_transactions(self.uid,{"tipo":"transferencia"})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["transferencia_id"],rows[1]["transferencia_id"])
    def test_backup_restore_is_user_scoped(self):
        cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"receita","Importação",250,"2026-02-02",cat,acc)
        backup=db.backup_db(self.uid)
        other=db.create_user("Destino","destino@example.com","senha-forte-000")
        msg=db.restore_backup(other,backup)
        self.assertIn("Backup importado",msg)
        self.assertEqual(len(db.list_transactions(other)),1)
        self.assertEqual(len(db.list_transactions(self.uid)),1)
    def test_edit_delete_scoped(self):
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        tid=db.add_transaction(self.uid,"despesa","Conta",12,"2026-01-10",cat,acc,"pendente")
        db.edit_transaction(self.uid,tid,"Conta editada",15,"2026-01-11",cat,acc,"pago","ok")
        self.assertEqual(db.list_transactions(self.uid)[0]["descricao"],"Conta editada")
        other=db.create_user("Outro","outro2@example.com","senha-forte-789")
        with self.assertRaises(ValueError): db.delete_transaction(other,tid)
        db.delete_transaction(self.uid,tid)
        self.assertEqual(db.list_transactions(self.uid),[])
    def test_money_brazilian_format(self):
        self.assertEqual(db.money("R$ 1.234,56"),db.Decimal("1234.56"))
        self.assertEqual(db.money("12,345"),db.Decimal("12.35"))
        with self.assertRaises(ValueError): db.money("abc")
    def test_card_invoice_installments_and_payment(self):
        expense_cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        card_id=None
        db.add_card(self.uid,"Visa",1000,20,5)
        card_id=db.cards(self.uid)[0]["id"]
        db.add_purchase(self.uid,card_id,"Compra parcelada",100,"2026-10-01",expense_cat,3)
        invoice=db.card_invoice(self.uid,card_id,"2026-10")
        self.assertEqual(invoice["total"],db.Decimal("33.34"))
        self.assertEqual(invoice["vencimento"],"2026-11-05")
        paid=db.pay_card_invoice(self.uid,card_id,"2026-10",10,acc,"2026-10-29","Pagamento parcial")
        self.assertEqual(paid["pago"],db.Decimal("10.00"))
        self.assertEqual(paid["aberto"],db.Decimal("23.34"))
        self.assertEqual(db.accounts(self.uid)[0]["saldo"],db.Decimal("-10.00"))
        payment_tx=[r for r in db.list_transactions(self.uid) if r["descricao"].startswith("Pagamento fatura")][0]
        with self.assertRaises(ValueError): db.edit_transaction(self.uid,payment_tx["id"],"Mudança",10,"2026-10-29",expense_cat,acc,"pago","")
        db.delete_transaction(self.uid,payment_tx["id"])
        self.assertEqual(db.card_invoice(self.uid,card_id,"2026-10")["pago"],db.Decimal("0.00"))
    def test_backup_restore_preserves_card_payment_linkage(self):
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_card(self.uid,"Master",500,20,8)
        card_id=db.cards(self.uid)[0]["id"]
        db.add_purchase(self.uid,card_id,"Compra",90,"2026-10-01",cat,1)
        db.pay_card_invoice(self.uid,card_id,"2026-10",90,acc,"2026-10-29")
        backup=db.backup_db(self.uid)
        other=db.create_user("Destino cartão","cartao@example.com","senha-forte-999")
        db.restore_backup(other,backup)
        restored_card=db.cards(other)[0]
        invoice=db.card_invoice(other,restored_card["id"],"2026-10")
        self.assertEqual(invoice["pago"],db.Decimal("90.00"))
        self.assertEqual(invoice["aberto"],db.Decimal("0.00"))
        payment_tx=[x for x in db.list_transactions(other) if x["descricao"].startswith("Pagamento fatura")]
        self.assertEqual(len(payment_tx),1)
        db.delete_transaction(other,payment_tx[0]["id"])
        self.assertEqual(db.card_invoice(other,restored_card["id"],"2026-10")["pago"],db.Decimal("0.00"))
    def test_recurring_generates_once_and_validates(self):
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_recurring(self.uid,"despesa","Aluguel",100,cat,acc,"Mensal","2020-01-31")
        first=db.run_recurring(self.uid)
        second=db.run_recurring(self.uid)
        self.assertGreater(first,0)
        self.assertEqual(second,0)
        rows=[r for r in db.list_transactions(self.uid) if r.get("recorrencia_id")]
        self.assertEqual(len(rows),first)
        self.assertTrue(all(r["recorrencia_id"] for r in rows))
    def test_budget_decimal_totals_and_category_validation(self):
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"despesa","A",0.10,"2026-10-01",cat,acc,"pago")
        db.add_transaction(self.uid,"despesa","B",0.20,"2026-10-02",cat,acc,"pago")
        db.add_budget(self.uid,cat,"2026-10",1)
        self.assertEqual(db.budgets(self.uid,"2026-10")[0]["gasto"],db.Decimal("0.30"))
        with self.assertRaises(ValueError): db.add_budget(self.uid,"Categoria inexistente","2026-10",100)
    def test_legacy_migration_read_only_and_one_time(self):
        legacy=Path(self.tmp.name)/"legacy.db"
        c=sqlite3.connect(legacy)
        c.executescript("CREATE TABLE categories(id INTEGER PRIMARY KEY,nome TEXT,tipo TEXT); CREATE TABLE transactions(id INTEGER PRIMARY KEY,tipo TEXT,descricao TEXT,valor REAL,data TEXT,categoria TEXT,conta TEXT,status TEXT,observacoes TEXT);")
        c.execute("INSERT INTO categories(nome,tipo) VALUES('Consultoria','receita')")
        c.execute("INSERT INTO transactions(tipo,descricao,valor,data,categoria,conta,status,observacoes) VALUES('receita','Serviço',123.45,'2025-01-02','Consultoria','Conta externa',NULL,'legado')")
        c.commit(); c.close()
        result=db.migrate_legacy(self.uid,legacy)
        self.assertTrue(result["ok"],result["message"])
        self.assertEqual(len(db.list_transactions(self.uid)),1)
        self.assertEqual(db.money(db.list_transactions(self.uid)[0]["valor"]),db.Decimal("123.45"))
        with self.assertRaises(sqlite3.OperationalError):
            ro=sqlite3.connect(f"file:{legacy.resolve()}?mode=ro",uri=True)
            try:
                ro.execute("INSERT INTO categories(nome,tipo) VALUES('x','despesa')")
            finally:
                ro.close()
        again=db.migrate_legacy(self.uid,legacy)
        self.assertFalse(again["ok"])

    def test_login_rate_limit_and_audit(self):
        for _ in range(5): db.authenticate("teste@example.com", "senha-incorreta")
        self.assertTrue(db.login_locked("teste@example.com"))
        self.assertIsNone(db.authenticate("teste@example.com", "senha-forte-123"))
        db.clear_login_failures("teste@example.com")
        self.assertIsNotNone(db.authenticate("teste@example.com", "senha-forte-123"))
        db.audit_event(self.uid, "teste", "evento de auditoria")
        self.assertEqual(db.audit_events(self.uid, 1)[0]["evento"], "teste")

    def test_mark_all_notifications_read_is_user_scoped(self):
        other=db.create_user("Outro","notifica@example.com","senha-forte-999")
        with db.conn() as c:
            c.execute("INSERT INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(self.uid,"A","B","a"))
            c.execute("INSERT INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(other,"A","B","b"))
        self.assertEqual(db.mark_all_notifications_read(self.uid),1)
        mine=db.notifications(self.uid)
        self.assertTrue(all(n["lida"] for n in mine))
        self.assertFalse(db.notifications(other)[0]["lida"])

    def test_backup_size_and_format_validation(self):
        with self.assertRaises(ValueError): db.restore_backup(self.uid, b"x"*(20*1024*1024+1))
        with self.assertRaises(ValueError): db.restore_backup(self.uid, '{"produto":"Outro","categories":[],"accounts":[],"transactions":[],"budgets":[],"cards":[],"card_purchases":[],"recurring":[],"notifications":[]}')

if __name__=="__main__": unittest.main()
