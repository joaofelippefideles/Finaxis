/* ---------- Transferências ---------- */

App.views.transfers = {
  route: "transfers",
  title: "Transferências",
  subtitle: "Movimentação entre contas",
  async render() {
    const accounts = await api("/accounts");
    const active = accounts.filter((a) => a.active);
    const opts = optionsHtml(active);
    App.data.accounts = accounts;
    const txns = await api("/transactions", { query: { type: "transferencia", limit: 50 } });
    let rows = "";
    for (const t of txns || []) {
      rows += `<tr>
        <td>${fmtDate(t.date)}</td>
        <td class="td-strong">${escapeHtml(t.description)}</td>
        <td>${t.from_account_id && t.account_name ? escapeHtml(t.account_name) : "—"}</td>
        <td>${t.card_name ? escapeHtml(t.card_name) : "—"}</td>
        <td class="text-right">${moneyCell(t.amount, "transferencia")}</td>
        <td>${statusBadge(t.status)}</td>
      </tr>`;
    }
    return `
      <div class="grid two">
        <div class="card">
          <div class="card__head"><h3>Nova transferência</h3></div>
          <div class="card__body">
            <form id="transfer-form" class="form-grid">
              ${fieldHtml({ id: "description", label: "Descrição", required: true, span2: true })}
              ${fieldHtml({ id: "amount", label: "Valor (R$)", placeholder: "0,00", required: true })}
              ${fieldHtml({ id: "date", label: "Data", type: "date", value: todayISO(), required: true })}
              ${fieldHtml({ id: "from_account_id", label: "Origem", type: "select", required: true, options: opts })}
              ${fieldHtml({ id: "to_account_id", label: "Destino", type: "select", required: true, options: opts, span2: false })}
              ${fieldHtml({ id: "observation", label: "Observação", type: "textarea", span2: true })}
              <div class="span2" style="margin-top:6px">
                <button class="btn btn--block" type="submit">${icon("arrow-left-right")} Transferir</button>
              </div>
            </form>
          </div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Histórico recente</h3></div>
          <div class="card__body table-wrap">
            <table class="data">
              <thead><tr><th>Data</th><th>Descrição</th><th>Origem</th><th>Destino</th><th class="text-right">Valor</th><th>Status</th></tr></thead>
              <tbody>${rows || `<tr><td colspan="6">${emptyHtml("Nenhuma transferência")}</td></tr>`}</tbody>
            </table>
          </div>
        </div>
      </div>`;
  },
  init() {
    document.getElementById("transfer-form")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      payload.amount = parseBrl(payload.amount);
      const btn = e.target.querySelector("button");
      btn.disabled = true;
      try {
        if (payload.from_account_id === payload.to_account_id) {
          throw new Error("As contas devem ser diferentes");
        }
        await api("/transfers", { method: "POST", body: payload });
        toast("Transferência realizada", "success");
        App.navigate("transfers");
      } catch (err) {
        toast(err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
  },
};