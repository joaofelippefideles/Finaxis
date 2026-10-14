/* ---------- Contas a receber ---------- */

App.views.receivables = {
  route: "receivables",
  title: "Contas a receber",
  subtitle: "Gerenciamento de recebimentos",
  groups: [
    ["todas", "Todas"],
    ["vencidos", "Vencidos"],
    ["hoje", "Hoje"],
    ["proximos", "Próximos 30d"],
    ["recebidos", "Recebidos"],
  ],
  async render() {
    const [items, categories, accounts] = await Promise.all([
      api("/receivables", { query: { group: App.data.recvGroup || "todas" } }),
      api("/categories"),
      api("/accounts"),
    ]);
    App.data.categories = categories;
    App.data.accounts = accounts;

    let rows = "";
    for (const p of items || []) {
      const overdue = p.status === "pendente" && p.is_overdue;
      rows += `<tr>
        <td class="td-strong" style="${overdue ? "color:var(--red)" : ""}">${escapeHtml(p.description)}</td>
        <td>${fmtDate(p.due_date)}</td>
        <td>${escapeHtml(p.observation || "—")}</td>
        <td class="text-right">${formatBRL(p.amount)}</td>
        <td>${statusBadge(p.status)}</td>
        <td>
          <div class="actions-cell">
            ${p.status === "pendente" ? `<button class="btn-icon" title="Receber" data-act="receive" data-id="${p.id}">${icon("check")}</button>` : ""}
            ${p.status === "recebido" ? `<button class="btn-icon" title="Reabrir" data-act="reopen" data-id="${p.id}">${icon("rotate-ccw")}</button>` : ""}
            ${p.status === "pendente" ? `<button class="btn-icon" title="Cancelar" data-act="cancel" data-id="${p.id}">${icon("x")}</button>` : ""}
            <button class="btn-icon" title="Editar" data-act="edit" data-id="${p.id}">${icon("edit-2")}</button>
            <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${p.id}">${icon("trash-2")}</button>
          </div>
        </td>
      </tr>`;
    }

    const tabs = this.groups.map(([g, label]) =>
      `<button class="tab ${(App.data.recvGroup || "todas") === g ? "active" : ""}" data-group="${g}">${label}</button>`
    ).join("");

    return `
      <div class="tabs">${tabs}</div>
      <div class="card">
        <div class="card__head"><h3>Contas a receber</h3><button class="btn" id="btn-new-receivable">${icon("plus")} Nova conta</button></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Descrição</th><th>Vencimento</th><th>Observação</th><th class="text-right">Valor</th><th>Status</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="6">${emptyHtml("Nenhuma conta a receber")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        App.data.recvGroup = tab.dataset.group;
        App.navigate("receivables");
      });
    });
    document.getElementById("btn-new-receivable")?.addEventListener("click", () => openListItemModal("receivables"));
    bindListItemActions("receivables");
  },
};