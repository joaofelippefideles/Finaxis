from __future__ import annotations
import io, os, shutil, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import database as db

st.set_page_config(page_title="Finaxis 2.0", page_icon="💠", layout="wide", initial_sidebar_state="expanded")
db.init_db()
theme_css = """
<style>
:root{--primary:#3B5BDB}
.block-container{max-width:1400px;padding-top:1.5rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:var(--secondary-background-color);border:1px solid #e4e8f0;padding:16px;border-radius:14px;box-shadow:0 2px 8px #1822300a}
div[data-testid="stForm"]{background:var(--secondary-background-color);border:1px solid #e4e8f0;padding:16px;border-radius:12px}
h1,h2,h3{letter-spacing:-.3px}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

def money(v): return db.fmt(v)
def notify_error(fn):
    try:
        result=fn()
        return True if result is None else result
    except Exception as e:
        st.error(str(e))
        return None

if "user_id" not in st.session_state: st.session_state.user_id=None
SESSION_TIMEOUT_MINUTES=30
if st.session_state.user_id:
    last=st.session_state.get("last_activity")
    if last and (datetime.now()-last).total_seconds()>SESSION_TIMEOUT_MINUTES*60:
        st.session_state.clear()
        st.warning("Sua sessão expirou por inatividade. Entre novamente.")
        st.rerun()
    st.session_state.last_activity=datetime.now()
if not st.session_state.user_id:
    left, right=st.columns([1.2,1])
    with left:
        st.markdown("# 💠 Finaxis 2.0")
        st.subheader("Sua vida financeira, organizada.")
        st.write("Controle receitas, despesas, contas, cartões, orçamentos e relatórios em um só lugar.")
        st.info("Cada conta possui dados isolados. Senhas são armazenadas com hash seguro.")
    with right:
        login_tab, signup_tab=st.tabs(["Entrar","Criar conta"])
        with login_tab:
            with st.form("login"):
                email=st.text_input("E-mail",key="login_email")
                senha=st.text_input("Senha",type="password",key="login_password")
                ok=st.form_submit_button("Entrar",use_container_width=True)
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
                ok=st.form_submit_button("Criar conta",use_container_width=True)
            if ok:
                if senha!=senha2: st.error("As senhas não coincidem.")
                else:
                    uid=notify_error(lambda: db.create_user(nome,email,senha))
                    if uid:
                        db.audit_event(uid,"conta_criada","Cadastro de usuário")
                        st.session_state.user_id=uid; st.session_state.last_activity=datetime.now(); st.success("Conta criada!"); st.rerun()
    st.stop()

uid=st.session_state.user_id
u=db.user(uid)
if not u:
    st.session_state.user_id=None; st.rerun()
if db.get_theme(uid)=="Escuro":
    st.markdown("""<style>
    .stApp{background:#111827;color:#f3f4f6}
    [data-testid="stMetric"],div[data-testid="stForm"],[data-testid="stExpander"]{background:#1f2937!important;color:#f3f4f6!important;border-color:#374151!important}
    [data-testid="stSidebar"]{background:#111827}
    </style>""",unsafe_allow_html=True)
db.run_recurring(uid)
notifs=db.notifications(uid)
with st.sidebar:
    st.markdown("## 💠 Finaxis 2.0")
    st.caption("Sessão protegida · expira após 30 minutos de inatividade")
    st.caption(f"Olá, {u['nome']}")
    page=st.radio("Navegação",["Visão geral","Lançamentos","Nova movimentação","Contas","Cartões de crédito","Orçamentos","Recorrências","Relatórios","Notificações","Categorias","Configurações"])
    st.divider()
    st.caption(f"{sum(1 for n in notifs if not n['lida'])} notificação(ões) não lida(s)")
    if st.button("Sair",use_container_width=True):
        db.audit_event(uid,"logout","Encerramento da sessão")
        st.session_state.clear(); st.rerun()

def tx_df(rows):
    if not rows: return pd.DataFrame(columns=["Data","Tipo","Descrição","Categoria","Conta","Valor","Status"])
    return pd.DataFrame([{"ID":r["id"],"Data":r["data"],"Tipo":r["tipo"].title(),"Descrição":r["descricao"],"Categoria":r["categoria"],"Conta":r["conta"],"Valor":float(db.money(r["valor"])),"Status":r["status"] or "Concluído","Observações":r.get("observacoes","")} for r in rows])
def tx_form(prefix, default_tipo="despesa"):
    tipo=st.selectbox("Tipo",["despesa","receita"],index=0 if default_tipo=="despesa" else 1,key=prefix+"tipo")
    cats=db.categories(uid,tipo); accs=db.accounts(uid)
    with st.form(prefix+"form"):
        descricao=st.text_input("Descrição")
        c1,c2,c3=st.columns(3)
        valor=c1.number_input("Valor (R$)",min_value=0.01,value=10.0,step=1.0,format="%.2f")
        data_l=c2.date_input("Data",value=date.today())
        categoria=c3.selectbox("Categoria",[x["nome"] for x in cats] or ["Outros"])
        conta=st.selectbox("Conta",[x["nome"] for x in accs] or ["Conta principal"])
        status=st.selectbox("Situação",["pendente","pago"]) if tipo=="despesa" else None
        obs=st.text_area("Observações",height=70)
        submit=st.form_submit_button("Salvar lançamento",use_container_width=True)
    if submit:
        result=notify_error(lambda: db.add_transaction(uid,tipo,descricao,valor,data_l.isoformat(),categoria,conta,status,obs))
        if result: st.success("Lançamento salvo."); st.rerun()

if page=="Visão geral":
    st.title("Visão geral")
    st.caption("Seu resumo financeiro e os próximos compromissos.")
    mes=date.today().strftime("%Y-%m")
    ini=date.today().replace(day=1).isoformat()
    resumo=db.summary(uid,ini,date.today().isoformat())
    # Monthly totals include all month's transactions, not just up to today.
    import calendar
    month_end=date.today().replace(day=calendar.monthrange(date.today().year,date.today().month)[1])
    allmonth=db.list_transactions(uid,{"inicio":ini,"fim":month_end.isoformat()})
    receitas=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="receita"),db.money(0))
    pagas=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="despesa" and x["status"]=="pago"),db.money(0))
    pend=sum((db.money(x["valor"]) for x in allmonth if x["tipo"]=="despesa" and x["status"]=="pendente"),db.money(0))
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Receitas do mês",money(receitas)); c2.metric("Despesas pagas",money(pagas)); c3.metric("Despesas pendentes",money(pend)); c4.metric("Saldo do período",money(receitas-pagas))
    import calendar
    first_day=date.today().replace(day=1)
    prev_first=first_day-timedelta(days=1)
    prev_start=prev_first.replace(day=1).isoformat()
    prev_rows=db.list_transactions(uid,{"inicio":prev_start,"fim":prev_first.isoformat()})
    prev_rec=sum(float(x["valor"]) for x in prev_rows if x["tipo"]=="receita")
    prev_desp=sum(float(x["valor"]) for x in prev_rows if x["tipo"]=="despesa" and x["status"]=="pago")
    st.caption(f"Mês anterior: receitas {money(prev_rec)} · despesas pagas {money(prev_desp)}")
    rows=db.list_transactions(uid,{"inicio":ini,"fim":date.today().isoformat()})
    a,b=st.columns(2)
    with a:
        st.subheader("Despesas por categoria")
        df=pd.DataFrame([{"Categoria":x["categoria"],"Valor":float(x["valor"])} for x in rows if x["tipo"]=="despesa"])
        if not df.empty: st.plotly_chart(px.pie(df,names="Categoria",values="Valor",hole=.55),use_container_width=True)
        else: st.info("Ainda não há despesas neste período.")
    with b:
        st.subheader("Evolução mensal")
        alltx=db.list_transactions(uid)
        if alltx:
            df=pd.DataFrame([{"Mês":x["data"][:7],"Tipo":x["tipo"].title(),"Valor":float(x["valor"])} for x in alltx if x["tipo"] in ("receita","despesa")])
            if not df.empty:
                agg=df.groupby(["Mês","Tipo"],as_index=False)["Valor"].sum()
                st.plotly_chart(px.bar(agg,x="Mês",y="Valor",color="Tipo",barmode="group"),use_container_width=True)
        else: st.info("Cadastre seu primeiro lançamento para visualizar a evolução.")
    st.subheader("Últimos lançamentos")
    st.dataframe(tx_df(db.list_transactions(uid)[:8]),use_container_width=True,hide_index=True)
    st.subheader("Orçamentos do mês")
    for bgt in db.budgets(uid,mes):
        lim=bgt["limite_valor"]; spent=bgt["gasto"]
        st.write(f'{bgt["categoria"]}: {money(spent)} / {money(lim)}')
        st.progress(min(1.0,float(spent/lim)) if lim else 0.0)

elif page=="Lançamentos":
    st.title("Lançamentos")
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
    st.dataframe(tx_df(rows),use_container_width=True,hide_index=True)
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
    with st.form("new_account"):
        nome=st.text_input("Nome da conta")
        tipo=st.selectbox("Tipo",["Conta corrente","Poupança","Carteira","Conta digital","Investimento","Outro"])
        saldo=st.number_input("Saldo inicial (R$)",value=0.0,step=50.0)
        go=st.form_submit_button("Adicionar conta")
    if go:
        result=notify_error(lambda: db.add_account(uid,nome,tipo,saldo))
        if result is not None: st.success("Conta adicionada."); st.rerun()
    accs=db.accounts(uid)
    st.dataframe(pd.DataFrame([{"Conta":a["nome"],"Tipo":a["tipo"],"Saldo atual":float(a["saldo"])} for a in accs]),use_container_width=True,hide_index=True)
    st.caption("O saldo considera receitas e despesas pagas. Transferências entre contas são exibidas no histórico; confira o saldo por conta.")

elif page=="Cartões de crédito":
    st.title("Cartões de crédito")
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
        st.dataframe(pd.DataFrame(card_rows),use_container_width=True,hide_index=True)
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
            st.dataframe(pd.DataFrame([{"Data":x["data"],"Cartão":x["cartao"],"Descrição":x["descricao"],"Categoria":x["categoria"],"Total":float(x["valor_total"]),"Parcelas":x["parcelas"],"Valor médio da parcela":float(db.money(x["valor_total"])/x["parcelas"])} for x in ps]),use_container_width=True,hide_index=True)
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
                    st.dataframe(pd.DataFrame([{"Compra":x["descricao"],"Data":x["data_compra"],"Parcela":f"{x['parcela']}/{x['parcelas']}", "Categoria":x["categoria"],"Valor":float(x["valor"])} for x in invoice["itens"]]),use_container_width=True,hide_index=True)
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
        elif spent>=lim*.8: st.warning("Atenção: você já utilizou 80% ou mais do orçamento.")

elif page=="Recorrências":
    st.title("Lançamentos recorrentes")
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
    if rs: st.dataframe(pd.DataFrame([{"Descrição":r["descricao"],"Tipo":r["tipo"],"Valor":float(r["valor"]),"Frequência":r["frequencia"],"Próxima data":r["proxima_data"],"Ativa":"Sim" if r["ativo"] else "Não"} for r in rs]),use_container_width=True,hide_index=True)
    st.caption("As recorrências vencidas são processadas ao abrir a aplicação. Revise os lançamentos gerados no histórico.")

elif page=="Relatórios":
    st.title("Relatórios e exportação")
    c1,c2,c3=st.columns(3); inicio=c1.date_input("Data inicial",value=date.today().replace(day=1)); fim=c2.date_input("Data final",value=date.today()); tipo_rel=c3.selectbox("Tipo",["Todos","receita","despesa","transferencia"])
    c4,c5=st.columns(2)
    cat_rel=c4.selectbox("Categoria",["Todos"]+[x["nome"] for x in db.categories(uid)])
    conta_rel=c5.selectbox("Conta",["Todos"]+[x["nome"] for x in db.accounts(uid)])
    if inicio>fim: st.error("A data inicial não pode ser posterior à data final."); st.stop()
    rows=db.list_transactions(uid,{"inicio":inicio.isoformat(),"fim":fim.isoformat(),"tipo":tipo_rel,"categoria":cat_rel,"conta":conta_rel})
    df=tx_df(rows)
    st.dataframe(df,use_container_width=True,hide_index=True)
    total_rec=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="receita"),db.money(0))
    total_desp=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="despesa" and x.get("status")=="pago"),db.money(0))
    pendentes=sum((db.money(x["valor"]) for x in rows if x["tipo"]=="despesa" and x.get("status")=="pendente"),db.money(0))
    a,b,c,d=st.columns(4); a.metric("Receitas",money(total_rec)); b.metric("Despesas pagas",money(total_desp)); c.metric("Despesas pendentes",money(pendentes)); d.metric("Resultado realizado",money(total_rec-total_desp))
    st.download_button("Exportar CSV",df.to_csv(index=False).encode("utf-8-sig"),"relatorio_finaxis.csv","text/csv")
    excel=io.BytesIO()
    with pd.ExcelWriter(excel,engine="openpyxl") as writer: df.to_excel(writer,index=False,sheet_name="Lançamentos")
    st.download_button("Exportar Excel (XLSX)",excel.getvalue(),"relatorio_finaxis.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        pdf=io.BytesIO(); doc=SimpleDocTemplate(pdf,pagesize=landscape(A4))
        data=[["Data","Tipo","Descrição","Categoria","Conta","Valor","Status"]]
        data += [[str(x["Data"]),str(x["Tipo"]),str(x["Descrição"])[:36],str(x["Categoria"]),str(x["Conta"]),money(x["Valor"]),str(x["Status"])] for x in df.to_dict("records")]
        story=[Paragraph("Finaxis 2.0 — Relatório financeiro",getSampleStyleSheet()["Title"]),Paragraph(f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}",getSampleStyleSheet()["Normal"]),Spacer(1,12),Table(data,repeatRows=1)]
        doc.build(story)
        st.download_button("Exportar PDF",pdf.getvalue(),"relatorio_finaxis.pdf","application/pdf")
    except Exception as e: st.warning(f"PDF indisponível neste ambiente: {e}")

elif page=="Notificações":
    st.title("Central de notificações")
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
    with st.form("newcat"):
        nome=st.text_input("Nome da categoria")
        tipo=st.selectbox("Tipo",["despesa","receita"])
        go=st.form_submit_button("Adicionar categoria")
    if go:
        result=notify_error(lambda: db.add_category(uid,nome,tipo))
        if result is not None: st.success("Categoria adicionada."); st.rerun()
    cats=db.categories(uid)
    st.dataframe(pd.DataFrame([{"ID":x["id"],"Nome":x["nome"],"Tipo":x["tipo"],"Ativa":bool(x["ativo"])} for x in cats]),use_container_width=True,hide_index=True)
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
            (st.success if result["ok"] else st.error)(result["message"])
            if result["ok"]: st.rerun()
    st.subheader("Aparência")
    theme_current=db.get_theme(uid)
    theme_choice=st.selectbox("Tema preferido",["Claro","Escuro"],index=0 if theme_current=="Claro" else 1)
    if st.button("Salvar tema"):
        db.save_theme(uid,theme_choice); st.success("Preferência de tema salva."); st.rerun()
    st.subheader("Backup pessoal")
    st.caption("O backup exporta somente os registros deste usuário. Guarde o arquivo em local privado.")
    st.download_button("Baixar backup dos meus dados (JSON)",db.backup_db(uid),f"finaxis_backup_usuario_{uid}.json","application/json")
    st.warning("O backup contém dados financeiros pessoais. Guarde-o em local privado.")
    st.subheader("Restaurar backup JSON")
    st.caption("A restauração adiciona lançamentos ao usuário atual; use preferencialmente em uma conta nova para evitar duplicidades.")
    uploaded=st.file_uploader("Selecione um backup Finaxis (.json)",type=["json"])
    confirm_restore=st.checkbox("Entendo que a restauração pode adicionar registros duplicados.")
    if uploaded and confirm_restore and st.button("Restaurar dados do arquivo"):
        result=notify_error(lambda: db.restore_backup(uid,uploaded.getvalue()))
        if result: st.success(result); st.rerun()
    st.subheader("Atividade recente da conta")
    events=db.audit_events(uid,50)
    if events: st.dataframe(pd.DataFrame([{"Evento":x["evento"],"Detalhe":x["detalhe"],"Data":x["criado_em"]} for x in events]),use_container_width=True,hide_index=True)
    else: st.caption("Ainda não há eventos registrados.")
    st.subheader("Alterar senha")
    with st.form("password_change"):
        atual=st.text_input("Senha atual",type="password")
        nova=st.text_input("Nova senha (mínimo 10 caracteres)",type="password")
        conf=st.text_input("Confirmar nova senha",type="password")
        go=st.form_submit_button("Alterar senha")
    if go:
        from database import verify_password, hash_password, conn
        with conn() as c: row=c.execute("SELECT password_hash FROM users WHERE id=?",(uid,)).fetchone()
        if not row or not verify_password(atual,row["password_hash"]): st.error("Senha atual incorreta.")
        elif nova!=conf: st.error("A confirmação não coincide.")
        else:
            try:
                ph=hash_password(nova)
                with conn() as c: c.execute("UPDATE users SET password_hash=? WHERE id=?",(ph,uid))
                st.success("Senha alterada.")
            except Exception as e: st.error(str(e))
