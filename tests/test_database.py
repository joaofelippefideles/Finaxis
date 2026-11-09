"""Testes automatizados da camada de persistência do Finaxis.

Este arquivo é a principal evidência de orientação a objetos no projeto.
DatabaseTests herda de unittest.TestCase, sobrescreve os métodos de ciclo de
vida setUp e tearDown e utiliza os métodos de asserção herdados da classe
base. Os testes usam um banco temporário para não alterar os dados reais.

Conceitos dos Temas 4 e 5 presentes: subprogramas, classes, objetos,
atributos de instância (self.tmp, self.uid), herança, sobrescrita de métodos,
polimorfismo por meio dos hooks chamados pelo unittest, tratamento de
exceções e uso de bibliotecas.
"""

import sqlite3
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
import database as db

class DatabaseTests(unittest.TestCase):
    """Agrupa os testes de banco e herda recursos de unittest.TestCase.

    CONCEITO: HERANÇA
    A classe entrega ao unittest um conjunto de métodos test_* e reutiliza
    assertEqual, assertTrue, assertRaises e outros métodos da superclasse.

    CONCEITO: SOBRESCRITA
    setUp e tearDown existem na classe base e são redefinidos aqui para
    preparar e limpar o ambiente antes/depois de cada teste.
    """

    def setUp(self):
        """Prepara um banco temporário isolado antes de cada teste.

        CONCEITO: ATRIBUTOS DE INSTÂNCIA
        self.tmp, self.uid e self.old_path pertencem ao objeto de teste e
        ficam disponíveis em todos os métodos da mesma instância.
        """
        self.tmp=tempfile.TemporaryDirectory()
        self.old_path=db.DB_PATH
        self.old_legacy=db.LEGACY_DB
        db.DB_PATH=Path(self.tmp.name)/"test.db"
        db.LEGACY_DB=Path(self.tmp.name)/"legacy.db"
        db.init_db()
        self.uid=db.create_user("Teste","teste@example.com","senha-forte-123")

    def tearDown(self):
        """Restaura os caminhos originais e apaga o diretório temporário.

        CONCEITO: MÉTODO SOBRESCRITO CHAMADO PELO FRAMEWORK
        O unittest chama tearDown automaticamente ao final de cada teste,
        mesmo que o teste falhe. Isso caracteriza polimorfismo: o framework
        chama o método pelo contrato da classe base, mas executa a versão
        definida nesta subclasse.
        """
        db.DB_PATH=self.old_path
        db.LEGACY_DB=self.old_legacy
        self.tmp.cleanup()
    def test_demo_admin_is_created_once_and_password_is_hashed(self):
        """Confere idempotência do admin e formato do hash salgado."""
        db.init_db()
        with db.conn() as c:
            admin = c.execute("SELECT id,role FROM users WHERE email=?",
                              (db.DEMO_ADMIN_EMAIL,)).fetchone()
        # CONCEITO: MÉTODOS DE ASSERÇÃO HERDADOS
        # assertIsNotNone e assertEqual vêm de unittest.TestCase.
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], "admin")
        with db.conn() as c:
            row = c.execute("SELECT password_hash FROM users WHERE email=?",
                            (db.DEMO_ADMIN_EMAIL,)).fetchone()
        self.assertIn(":", row["password_hash"])
        self.assertRegex(row["password_hash"], r"^[0-9a-f]{32}:[0-9a-f]{64}$")
        before = row["password_hash"]
        db.init_db()
        with db.conn() as c:
            after = c.execute("SELECT password_hash FROM users WHERE email=?",
                              (db.DEMO_ADMIN_EMAIL,)).fetchone()["password_hash"]
        self.assertEqual(before, after)

    def test_password_and_isolation(self):
        """Verifica autenticação e isolamento dos dados entre usuários."""
        self.assertIsNotNone(db.authenticate("teste@example.com","senha-forte-123"))
        other=db.create_user("Outro","outro@example.com","senha-forte-456")
        acc=db.accounts(self.uid)[0]["nome"]
        cat=db.categories(self.uid,"receita")[0]["nome"]
        db.add_transaction(self.uid,"receita","Salário",1000,"2026-01-10",cat,acc)
        self.assertEqual(len(db.list_transactions(self.uid)),1)
        self.assertEqual(len(db.list_transactions(other)),0)
    def test_transfer_atomic_balances(self):
        """Confere que a transferência gera duas pontas e saldos opostos."""
        # CONCEITO: LIST COMPREHENSION E DICT COMPREHENSION
        names=[a["nome"] for a in db.accounts(self.uid)]
        db.add_transfer(self.uid,"Transferência",50,"2026-01-10",names[0],names[1])
        balances={a["nome"]:a["saldo"] for a in db.accounts(self.uid)}
        self.assertEqual(balances[names[0]],db.money(-50))
        self.assertEqual(balances[names[1]],db.money(50))
        rows=db.list_transactions(self.uid,{"tipo":"transferencia"})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["transferencia_id"],rows[1]["transferencia_id"])
    def test_backup_restore_is_user_scoped(self):
        """Garante que a restauração afeta somente o usuário de destino."""
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
        """Verifica edição, exclusão e bloqueio de acesso por outro usuário."""
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
        """Valida conversão de formatos brasileiros e rejeição de texto inválido."""
        self.assertEqual(db.money("R$ 1.234,56"),db.Decimal("1234.56"))
        self.assertEqual(db.money("12,345"),db.Decimal("12.35"))
        with self.assertRaises(ValueError): db.money("abc")
    def test_card_invoice_installments_and_payment(self):
        """Testa parcelamento, vencimento, pagamento parcial e estorno."""
        # CONCEITO: ASSERTRAISES COMO TESTE DE EXCEÇÃO
        # O bloco with self.assertRaises confirma que a operação inválida
        # lança ValueError, em vez de apenas verificar o valor de retorno.
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
        """Confirma que IDs de pagamento de fatura são remapeados na restauração."""
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
        """Garante que uma recorrência não gera lançamentos duplicados."""
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
    def test_monthly_recurring_keeps_original_day_after_february(self):
        """Valida a âncora mensal: dia 31 vira 28 em fevereiro e volta a 31 em março."""
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_recurring(self.uid,"despesa","Aluguel âncora",100,cat,acc,"Mensal","2025-01-31")
        db.run_recurring(self.uid)
        dates=sorted(r["data"] for r in db.list_transactions(self.uid) if r["descricao"]=="Aluguel âncora")
        self.assertIn("2025-01-31",dates)
        self.assertIn("2025-02-28",dates)
        self.assertIn("2025-03-31",dates)

    def test_daily_recurring_processing_is_bounded(self):
        """Confirma que o limite de ocorrências por execução é respeitado."""
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_recurring(self.uid,"despesa","Diária antiga",1,cat,acc,"Diária","2000-01-01")
        created=db.run_recurring(self.uid,max_occurrences_per_recurring=10)
        self.assertEqual(created,10)
        rec=db.recurrings(self.uid)[0]
        self.assertGreater(date.fromisoformat(rec["proxima_data"]),date(2000,1,10))
        self.assertLessEqual(date.fromisoformat(rec["proxima_data"]),date.today())

    def test_currency_format_supports_brl_usd_eur(self):
        """Verifica os símbolos das três moedas suportadas."""
        # CONCEITO: MÉTODOS DE STRING NOS TESTES
        # startswith confirma o prefixo esperado em cada moeda.
        self.assertTrue(db.fmt("1234.56","BRL").startswith("R$"))
        self.assertTrue(db.fmt("1234.56","USD").startswith("US$"))
        self.assertTrue(db.fmt("1234.56","EUR").startswith("€"))

    def test_budget_decimal_totals_and_category_validation(self):
        """Verifica soma exata com Decimal e validação de categoria do orçamento."""
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"despesa","A",0.10,"2026-10-01",cat,acc,"pago")
        db.add_transaction(self.uid,"despesa","B",0.20,"2026-10-02",cat,acc,"pago")
        db.add_budget(self.uid,cat,"2026-10",1)
        self.assertEqual(db.budgets(self.uid,"2026-10")[0]["gasto"],db.Decimal("0.30"))
        with self.assertRaises(ValueError): db.add_budget(self.uid,"Categoria inexistente","2026-10",100)
    def test_legacy_migration_read_only_and_one_time(self):
        """Migra dados legados e confirma abertura somente leitura e execução única."""
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
        """Verifica bloqueio após cinco falhas, liberação e registro de auditoria."""
        # CONCEITO: LAÇO FOR COM VARIÁVEL DESCARTÁVEL
        # _ indica que o valor da repetição não será usado.
        for _ in range(5): db.authenticate("teste@example.com", "senha-incorreta")
        self.assertTrue(db.login_locked("teste@example.com"))
        self.assertIsNone(db.authenticate("teste@example.com", "senha-forte-123"))
        db.clear_login_failures("teste@example.com")
        self.assertIsNotNone(db.authenticate("teste@example.com", "senha-forte-123"))
        db.audit_event(self.uid, "teste", "evento de auditoria")
        self.assertEqual(db.audit_events(self.uid, 1)[0]["evento"], "teste")

    def test_login_lock_resets_after_expiration_and_old_window(self):
        """Simula expiração do bloqueio alterando as datas no banco."""
        for _ in range(5):
            db.authenticate("teste@example.com", "senha-incorreta")
        self.assertTrue(db.login_locked("teste@example.com"))
        with db.conn() as c:
            c.execute("UPDATE login_attempts SET locked_until=?,updated_at=? WHERE email=?",
                      ("2000-01-01T00:00:00","2000-01-01T00:00:00","teste@example.com"))
        self.assertFalse(db.login_locked("teste@example.com"))
        self.assertIsNotNone(db.authenticate("teste@example.com", "senha-forte-123"))

    def test_change_password_requires_current_and_enforces_length(self):
        """Confirma exigência da senha atual e do tamanho mínimo da nova senha."""
        with self.assertRaises(ValueError):
            db.change_password(self.uid,"senha-errada","nova-senha-123")
        with self.assertRaises(ValueError):
            db.change_password(self.uid,"senha-forte-123","curta")
        self.assertTrue(db.change_password(self.uid,"senha-forte-123","nova-senha-123"))
        self.assertIsNotNone(db.authenticate("teste@example.com","nova-senha-123"))
        self.assertIsNone(db.authenticate("teste@example.com","senha-forte-123"))

    def test_restore_rejects_unsupported_schema_version(self):
        """Rejeita backup de versão de esquema desconhecida."""
        payload={"produto":"Finaxis 2.0","schema_version":999,
          "categories":[],"accounts":[],"transactions":[],"budgets":[],
          "cards":[],"card_purchases":[],"recurring":[],"notifications":[]}
        with self.assertRaisesRegex(ValueError,"Versão de backup"):
            db.restore_backup(self.uid,json.dumps(payload).encode("utf-8"))


    def test_report_filters_status_and_description_search(self):
        """Testa filtros combinados de status, período, tipo e busca textual."""
        expense_cat=db.categories(self.uid,"despesa")[0]["nome"]
        income_cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"despesa","Internet residencial",120,"2026-11-02",expense_cat,acc,"pago","provedor fibra")
        db.add_transaction(self.uid,"despesa","Energia elétrica",85,"2026-11-03",expense_cat,acc,"pendente","conta mensal")
        db.add_transaction(self.uid,"receita","Projeto consultoria",500,"2026-11-04",income_cat,acc,None,"cliente alfa")
        paid=db.list_transactions(self.uid,{"status":"pago"})
        self.assertEqual([r["descricao"] for r in paid],["Internet residencial"])
        completed=db.list_transactions(self.uid,{"status":"Concluído"})
        self.assertEqual({r["descricao"] for r in completed},{"Projeto consultoria"})
        searched=db.list_transactions(self.uid,{"busca":"fibra"})
        self.assertEqual([r["descricao"] for r in searched],["Internet residencial"])
        searched_obs=db.list_transactions(self.uid,{"busca":"cliente alfa"})
        self.assertEqual([r["descricao"] for r in searched_obs],["Projeto consultoria"])
        combined=db.list_transactions(self.uid,{"inicio":"2026-11-01","fim":"2026-11-30","tipo":"despesa","status":"pendente","busca":"energia"})
        self.assertEqual([r["descricao"] for r in combined],["Energia elétrica"])


    def test_backup_checksum_detects_modified_payload(self):
        """Detecta adulteração de backup pela divergência do checksum."""
        cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"receita","Receita teste",150,"2026-11-01",cat,acc)
        payload=json.loads(db.backup_db(self.uid).decode("utf-8"))
        payload["transactions"][0]["descricao"]="Conteúdo adulterado"
        with self.assertRaisesRegex(ValueError,"integridade"):
            db.restore_backup(self.uid,json.dumps(payload).encode("utf-8"))
        self.assertEqual(len(db.list_transactions(self.uid)),1)

    def test_same_backup_cannot_be_restored_twice(self):
        """Confirma a idempotência da restauração do mesmo arquivo."""
        cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"receita","Receita original",200,"2026-11-02",cat,acc)
        backup=db.backup_db(self.uid)
        other=db.create_user("Destino backup","backupdest@example.com","senha-forte-456")
        first=db.restore_backup(other,backup)
        second=db.restore_backup(other,backup)
        self.assertIn("restaurado com sucesso",first)
        self.assertIn("já foi restaurado",second)
        self.assertEqual(len(db.list_transactions(other)),1)

    def test_database_health_reports_integrity(self):
        """Verifica o relatório de integridade e contagens do banco."""
        health=db.database_health(self.uid)
        self.assertTrue(health["ok"])
        self.assertEqual(health["integrity"],["ok"])
        self.assertIn("transactions",health["counts"])

    def test_backup_rejects_invalid_transaction_before_writing(self):
        """Garante que dados inválidos são rejeitados antes de qualquer gravação."""
        payload=json.loads(db.backup_db(self.uid).decode("utf-8"))
        payload["integrity_sha256"]=db._backup_fingerprint(payload)
        payload["transactions"]=[{"tipo":"despesa","descricao":"Inválida","valor":"abc","data":"2026-99-99"}]
        payload["integrity_sha256"]=db._backup_fingerprint(payload)
        before=len(db.list_transactions(self.uid))
        with self.assertRaisesRegex(ValueError,"valor ou data inválida"):
            db.restore_backup(self.uid,json.dumps(payload).encode("utf-8"))
        self.assertEqual(len(db.list_transactions(self.uid)),before)


    def test_restore_accepts_legacy_v2_backup_without_checksum(self):
        """Aceita backups compatíveis anteriores à inclusão do checksum."""
        cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"receita","Legado compatível",75,"2026-11-05",cat,acc)
        payload=json.loads(db.backup_db(self.uid).decode("utf-8"))
        payload.pop("integrity_sha256",None)
        other=db.create_user("Legado","legacybackup@example.com","senha-forte-456")
        result=db.restore_backup(other,json.dumps(payload).encode("utf-8"))
        self.assertIn("Backup importado",result)
        self.assertEqual(len(db.list_transactions(other)),1)

    def test_transaction_submission_key_is_idempotent(self):
        """Confirma que a mesma chave de envio não duplica lançamento."""
        cat=db.categories(self.uid,"despesa")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        first=db.add_transaction(self.uid,"despesa","Teste anti duplicidade",42,
                                 "2026-11-09",cat,acc,"pago",submission_key="request-123")
        second=db.add_transaction(self.uid,"despesa","Teste anti duplicidade",42,
                                  "2026-11-09",cat,acc,"pago",submission_key="request-123")
        self.assertEqual(first,second)
        rows=db.list_transactions(self.uid,{"busca":"Teste anti duplicidade"})
        self.assertEqual(len(rows),1)

    def test_different_submission_keys_allow_same_value(self):
        """Permite lançamentos iguais quando as chaves de envio são diferentes."""
        cat=db.categories(self.uid,"receita")[0]["nome"]
        acc=db.accounts(self.uid)[0]["nome"]
        db.add_transaction(self.uid,"receita","Dois recebimentos",10,"2026-11-09",cat,acc,
                           submission_key="request-a")
        db.add_transaction(self.uid,"receita","Dois recebimentos",10,"2026-11-09",cat,acc,
                           submission_key="request-b")
        self.assertEqual(len(db.list_transactions(self.uid,{"busca":"Dois recebimentos"})),2)

    def test_mark_all_notifications_read_is_user_scoped(self):
        """Confirma que a leitura em massa não afeta notificações de outro usuário."""
        other=db.create_user("Outro","notifica@example.com","senha-forte-999")
        with db.conn() as c:
            c.execute("INSERT INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(self.uid,"A","B","a"))
            c.execute("INSERT INTO notifications(user_id,titulo,mensagem,chave) VALUES(?,?,?,?)",(other,"A","B","b"))
        self.assertEqual(db.mark_all_notifications_read(self.uid),1)
        mine=db.notifications(self.uid)
        self.assertTrue(all(n["lida"] for n in mine))
        self.assertFalse(db.notifications(other)[0]["lida"])

    def test_backup_size_and_format_validation(self):
        """Rejeita backup acima de 20 MB e arquivo de produto incompatível."""
        with self.assertRaises(ValueError): db.restore_backup(self.uid, b"x"*(20*1024*1024+1))
        with self.assertRaises(ValueError): db.restore_backup(self.uid, '{"produto":"Outro","categories":[],"accounts":[],"transactions":[],"budgets":[],"cards":[],"card_purchases":[],"recurring":[],"notifications":[]}')

if __name__=="__main__": unittest.main()
