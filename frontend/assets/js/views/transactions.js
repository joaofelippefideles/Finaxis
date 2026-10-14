/* ---------- Lançamentos ---------- */

let txnFilters = { type: "", status: "", search: "", start_date: "", end_date: "", page: 0 };

App.views.transactions = {
  route: "transactions",
  title: "Lançamentos",
  subtitle: "Receitas, despesas e transferências",
  async render() {
    const [categories, accounts, cards, txns] = await Promise.all([
      api("/categories"),
      api("/accounts"),
      api("/cards"),
      api("/transactions", { query: txnFilters }),
    ]);
    App.data.categories = categories;
    App.data.accounts = accounts;
    App.data.cards = cards;

    const catSel = optionsHtml(categories.filter((c) => c.active));
    const accSel = optionsHtml(accounts.filter((a) => a.active));

    let rows = "";
    for (const t of txns || []) {
      rows += `<tr>
        <td>${fmtDate(t.date)}</td>
        <td class="td-strong">${escapeHtml(t.description)}</td>
        <td>${escapeHtml(t.category_name || "—")}</td>
        <td>${escapeHtml(t.account_name || (t.card_name ? "Cartão" : "—"))}</td>
        <td>${typeBadge(t.type)}</td>
        <td>${statusBadge(t.status)}</td>
        <td class="text-right">${moneyCell(t.amount, t.type)}</td>
        <td>
          <div class="actions-cell">
            ${t.status === "pendente" ? `<button class="btn-icon" title="Pagar/Receber" data-act="pay" data-id="${t.id}">${icon("check")}</button>` : ""}
            <button class="btn-icon" title="Editar" data-act="edit" data-id="${t.id}">${icon("edit-2")}</button>
            ${t.status !== "cancelado" ? `<button class="btn-icon" title="Cancelar" data-act="cancel" data-id="${t.id}">${icon("x")}</button>` : ""}
            <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${t.id}">${icon("trash-2")}</button>
          </div>
        </td>
      </tr>`;
    }

    return `
      <div class="card">
        <div class="card__head">
          <div class="filters">
            <select id="f-type" class="input" style="width:150px">
              <option value="">Tipo</option>
              <option value="receita" ${txnFilters.type === "receita" ? "selected" : ""}>Receita</option>
              <option value="despesa" ${txnFilters.type === "despesa" ? "selected" : ""}>Despesa</option>
              <option value="transferencia" ${txnFilters.type === "transferencia" ? "selected" : ""}>Transferência</option>
            </select>
            <select id="f-status" class="input" style="width:150px">
              <option value="">Status</option>
              <option value="pendente" ${txnFilters.status === "pendente" ? "selected" : ""}>Pendente</option>
              <option value="pago" ${txnFilters.status === "pago" ? "selected" : ""}>Pago</option>
              <option value="recebido" ${txnFilters.status === "recebido" ? "selected" : ""}>Recebido</option>
              <option value="cancelado" ${txnFilters.status === "cancelado" ? "selected" : ""}>Cancelado</option>
            </select>
            <input id="f-start" type="date" class="input" value="${txnFilters.start_date}">
            <span class="text-muted">até</span>
            <input id="f-end" type="date" class="input" value="${txnFilters.end_date}">
            <input id="f-search" class="input" style="width:180px" placeholder="Buscar descrição" value="${escapeHtml(txnFilters.search)}">
          </div>
          <button class="btn" id="btn-new-txn">${icon("plus")} Novo lançamento</button>
        </div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Conta/Cartão</th><th>Tipo</th><th>Status</th><th class="text-right">Valor</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="8">${emptyHtml()}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    const q = (id) => document.getElementById(id);
    ["f-type", "f-status", "f-start", "f-end", "f-search"].forEach((id) => {
      q(id)?.addEventListener("change", (e) => {
        txnFilters[{ "f-type": "type", "f-status": "status", "f-start": "start_date", "f-end": "end_date", "f-search": "search" }[id]] = e.target.value;
        App.navigate("transactions");
      });
      if (id === "f-search") {
        q(id)?.addEventListener("keydown", (e) => {
          if (e.key === "Enter") {
            txnFilters.search = q(id).value;
            App.navigate("transactions");
          }
        });
      }
    });

    q("btn-new-txn")?.addEventListener("click", () => openTxnModal());

    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        if (act === "pay") {
          try {
            await api(`/transactions/${id}/pay`, { method: "POST" });
            toast("Lançamento quitado", "success");
            App.navigate("transactions");
          } catch (err) { toast(err.message, "error"); }
        } else if (act === "cancel") {
          confirmDialog("Cancelar este lançamento?", async () => {
            try {
              await api(`/transactions/${id}/cancel`, { method: "POST" });
              toast("Lançamento cancelado", "success");
              App.navigate("transactions");
            } catch (err) { toast(err.message, "error"); }
          });
        } else if (act === "del") {
          confirmDialog("Excluir definitivamente este lançamento?", async () => {
            try {
              await api(`/transactions/${id}`, { method: "DELETE" });
              toast("Lançamento excluído", "success");
              App.navigate("transactions");
            } catch (err) { toast(err.message, "error"); }
          }, "Excluir");
        } else if (act === "edit") {
          const t = (await api(`/transactions`)).find((x) => x.id === id);
          if (t) openTxnModal(t);
        }
      });
    });
  },
};

function openTxnModal(txn) {
  const types = ["receita", "despesa"];
  const statuses = ["pendente", "pago", "recebido", "cancelado"];
  const cats = (App.data.categories || []).filter((c) => c.active);
  const accs = (App.data.accounts || []).filter((a) => a.active);
  const cards = (App.data.cards || []).filter((c) => c.status === "ativo");

  const isInstallment = txn && txn.is_installment;
  const fields = modalFormHtml({
    id: "modal-txn",
    title: txn ? "Editar lançamento" : "Novo lançamento",
    size: "modal--lg",
    submitText: txn ? "Salvar" : "Criar",
    fieldsHtml:
      fieldHtml({ id: "description", label: "Descrição", value: txn?.description || "", required: true, span2: true }) +
      fieldHtml({ id: "amount", label: "Valor (R$)", type: "text", value: txn ? String(txn.amount) : "", placeholder: "0,00", required: true }) +
      fieldHtml({ id: "type", label: "Tipo", type: "select", required: true, options: types.map((t) => `<option value="${t}" ${txn?.type === t ? "selected" : ""}>${ucfirst(t)}</option>`).join("") }) +
      fieldHtml({ id: "date", label: "Data", type: "date", value: txn?.date || todayISO(), required: true }) +
      fieldHtml({ id: "status", label: "Status", type: "select", options: statuses.map((s) => `<option value="${s}" ${txn?.status === s ? "selected" : ""}>${ucfirst(s)}</option>`).join("") }) +
      fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats, txn?.category_id, "Sem categoria") }) +
      fieldHtml({ id: "account_id", label: "Conta", type: "select", options: optionsHtml(accs, txn?.account_id) }) +
      fieldHtml({ id: "card_id", label: "Cartão", type: "select", options: optionsHtml(cards, txn?.card_id) }) +
      (isInstallment ? "" : fieldHtml({ id: "installments_total", label: "Parcelas (compras no cartão)", type: "number", value: "", placeholder: "2 a 120", span2: true })) +
      fieldHtml({ id: "observation", label: "Observação", type: "textarea", value: txn?.observation || "", span2: true }),
    onSubmit: async (payload) => {
      for (const f of ["category_id", "account_id", "card_id"]) {
        if (!payload[f]) delete payload[f];
      }
      payload.amount = parseBrl(payload.amount);
      if (!payload.installments_total) delete payload.installments_total;
      const body = {};
      if (txn) {
        const upd = { description: payload.description, amount: payload.amount, date: payload.date, status: payload.status, observation: payload.observation };
        if (payload.category_id) upd.category_id = payload.category_id;
        if (payload.account_id) upd.account_id = payload.account_id;
        if (payload.card_id) upd.card_id = payload.card_id;
        await api(`/transactions/${txn.id}`, { method: "PUT", body: upd });
        toast("Lançamento atualizado", "success");
      } else {
        body.description = payload.description;
        body.amount = payload.amount;
        body.type = payload.type;
        body.date = payload.date;
        body.status = payload.status;
        if (payload.category_id) body.category_id = payload.category_id;
        if (payload.account_id) body.account_id = payload.account_id;
        if (payload.card_id) body.card_id = payload.card_id;
        if (payload.installments_total) body.installments_total = Number(payload.installments_total);
        if (payload.observation) body.observation = payload.observation;
        await api("/transactions", { method: "POST", body });
        const count = body.installments_total ? body.installments_total : 1;
        toast(`Lançamento criado${count > 1 ? " em " + count + " parcelas" : ""}`, "success");
      }
      App.navigate("transactions");
    },
  });

  const typeSel = fields.querySelector("#type");
  const catSelEl = fields.querySelector("#category_id");
  const updateCats = () => {
    const t = typeSel.value;
    catSelEl.innerHTML = optionsHtml(cats.filter((c) => c.active && c.type === t), "", "Sem categoria");
  };
  updateCats();
  typeSel.addEventListener("change", updateCats);
}