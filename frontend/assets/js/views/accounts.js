/* ---------- Contas ---------- */

App.views.accounts = {
  route: "accounts",
  title: "Contas bancárias",
  subtitle: "Saldo, instituição e perfil",
  async render() {
    const accounts = await api("/accounts", { query: { include_inactive: true } });
    App.data.accounts = accounts;
    let rows = "";
    for (const a of accounts || []) {
      rows += `<tr>
        <td class="td-strong">${escapeHtml(a.name)}</td>
        <td>${escapeHtml(a.bank || "—")}</td>
        <td>${escapeHtml(a.type.replace("_", " "))}</td>
        <td>${escapeHtml(a.account_number || "—")}</td>
        <td class="text-right">${formatBRL(a.balance)}</td>
        <td>${a.active ? '<span class="badge badge--green">Ativa</span>' : '<span class="badge badge--gray">Inativa</span>'}</td>
        <td>
          <div class="actions-cell">
            <button class="btn-icon" title="Editar" data-act="edit" data-id="${a.id}">${icon("edit-2")}</button>
            <button class="btn-icon" title="${a.active ? "Desativar" : "Ativar"}" data-act="toggle" data-id="${a.id}">${icon(a.active ? "toggle-left" : "toggle-right")}</button>
            <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${a.id}">${icon("trash-2")}</button>
          </div>
        </td>
      </tr>`;
    }
    const total = (accounts || []).reduce((acc, a) => acc + parseFloat(a.balance || 0), 0);
    return `
      <div class="stat stat--accent" style="max-width:280px;margin-bottom:16px">
        <span class="stat__label">Saldo consolidado</span>
        <span class="stat__value">${formatBRL(total)}</span>
      </div>
      <div class="card">
        <div class="card__head"><h3>Contas</h3><button class="btn" id="btn-new-account">${icon("plus")} Nova conta</button></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Nome</th><th>Banco</th><th>Tipo</th><th>Nº conta</th><th class="text-right">Saldo</th><th>Status</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="7">${emptyHtml("Nenhuma conta cadastrada")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    document.getElementById("btn-new-account")?.addEventListener("click", () => openAccountModal());
    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        const acc = (App.data.accounts || []).find((a) => a.id === id);
        if (act === "edit") {
          openAccountModal(acc);
        } else if (act === "toggle") {
          try {
            await api(`/accounts/${id}`, { method: "PUT", body: { active: !acc.active } });
            toast("Conta atualizada", "success");
            App.navigate("accounts");
          } catch (err) { toast(err.message, "error"); }
        } else if (act === "del") {
          confirmDialog(`Excluir a conta "${acc.name}"?`, async () => {
            try {
              await api(`/accounts/${id}`, { method: "DELETE" });
              toast("Conta excluída", "success");
              App.navigate("accounts");
            } catch (err) { toast(err.message, "error"); }
          });
        }
      });
    });
  },
};

function openAccountModal(acc) {
  const types = ["conta_corrente", "poupanca", "carteira", "conta_digital", "investimentos"];
  modalFormHtml({
    id: "modal-account",
    title: acc ? "Editar conta" : "Nova conta",
    submitText: acc ? "Salvar" : "Criar",
    fieldsHtml:
      fieldHtml({ id: "name", label: "Nome", value: acc?.name || "", placeholder: "Ex.: Nubank", required: true, span2: true }) +
      fieldHtml({ id: "bank", label: "Banco", value: acc?.bank || "" }) +
      fieldHtml({ id: "type", label: "Tipo", type: "select", options: types.map((t) => `<option value="${t}" ${acc?.type === t ? "selected" : ""}>${t.replace("_", " ")}</option>`).join(""), required: true }) +
      fieldHtml({ id: "initial_balance", label: "Saldo inicial", value: acc ? String(acc.initial_balance ?? 0) : "0", placeholder: "0,00" }) +
      fieldHtml({ id: "agency", label: "Agência", value: acc?.agency || "" }) +
      fieldHtml({ id: "account_number", label: "Nº conta", value: acc?.account_number || "" }),
    onSubmit: async (payload) => {
      payload.initial_balance = parseBrl(payload.initial_balance);
      const method = acc ? "PUT" : "POST";
      const endpoint = acc ? `/accounts/${acc.id}` : "/accounts";
      if (acc && payload.initial_balance) delete payload.initial_balance;
      await api(endpoint, { method, body: payload });
      toast(acc ? "Conta atualizada" : "Conta criada", "success");
      App.navigate("accounts");
    },
  });
}