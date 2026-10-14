/* ---------- Orçamento ---------- */

App.views.budgets = {
  route: "budgets",
  title: "Orçamento",
  subtitle: "Limites de gastos por categoria",
  async render() {
    const month = App.data.budgetMonth || currentMonth();
    const [data, categories] = await Promise.all([
      api("/budgets", { query: { month } }),
      api("/categories", { query: { type: "despesa" } }),
    ]);
    App.data.categories = categories;

    let items = "";
    for (const b of data.items || []) {
      const pct = Number(b.percent);
      const cls = b.level === "critical" ? "critical" : b.level === "warn" ? "warn" : "";
      items += `<div class="budget-row">
        <div class="budget-row__top">
          <span class="budget-row__name">${escapeHtml(b.category_name)}</span>
          <div style="display:flex;align-items:center;gap:10px">
            <span class="text-muted">${formatBRL(b.spent)} / ${formatBRL(b.limit_amount)}</span>
            <span class="badge ${b.level === "critical" ? "badge--red" : b.level === "warn" ? "badge--amber" : "badge--green"}">${pct.toFixed(0)}%</span>
            <div class="actions-cell">
              <button class="btn-icon" title="Editar" data-act="edit" data-id="${b.id}">${icon("edit-2")}</button>
              <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${b.id}">${icon("trash-2")}</button>
            </div>
          </div>
        </div>
        <div class="progress ${cls}"><div style="width:${Math.min(pct, 100)}%"></div></div>
        <div style="margin-top:5px;font-size:12px;color:var(--text-muted)">
          ${b.remaining >= 0 ? `Restam ${formatBRL(b.remaining)}` : `<span style="color:var(--red)">Estourado em ${formatBRL(Math.abs(b.remaining))}</span>`}
        </div>
      </div>`;
    }

    return `
      <div class="grid two">
        <div class="card">
          <div class="card__head">
            <h3>Orçamento · <input type="month" id="b-month" class="input" style="width:auto;padding:5px 10px" value="${month}"></h3>
            <button class="btn" id="btn-new-budget">${icon("plus")} Nova meta</button>
          </div>
          <div class="card__body">
            <div style="display:flex;gap:16px;margin-bottom:6px">
              <div class="stat" style="box-shadow:none;padding:10px 12px">
                <span class="stat__label">Orçado</span>
                <span class="stat__value" style="font-size:17px">${formatBRL(data.total_limit)}</span>
              </div>
              <div class="stat" style="box-shadow:none;padding:10px 12px">
                <span class="stat__label">Gasto</span>
                <span class="stat__value" style="font-size:17px">${formatBRL(data.total_spent)}</span>
              </div>
            </div>
            ${items || emptyHtml("Nenhum orçamento definido neste mês")}
          </div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Status do mês</h3></div>
          <div class="card__body">
            <div class="chart-box"><canvas id="chart-budget"></canvas></div>
          </div>
        </div>
      </div>`;
  },
  async init() {
    const monthEl = document.getElementById("b-month");
    monthEl?.addEventListener("change", () => {
      App.data.budgetMonth = monthEl.value;
      App.navigate("budgets");
    });
    document.getElementById("btn-new-budget")?.addEventListener("click", () => openBudgetModal());
    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        const data = await api("/budgets", { query: { month: App.data.budgetMonth || currentMonth() } });
        const b = data.items.find((x) => x.id === id);
        if (act === "del") {
          confirmDialog(`Excluir orçamento de "${b.category_name}"?`, async () => {
            try {
              await api(`/budgets/${id}`, { method: "DELETE" });
              toast("Orçamento excluído", "success");
              App.navigate("budgets");
            } catch (err) { toast(err.message, "error"); }
          });
        } else if (act === "edit") {
          openBudgetModal(b);
        }
      });
    });

    const month = App.data.budgetMonth || currentMonth();
    const data = await api("/budgets", { query: { month } });
    App.charts["chart-budget"]?.destroy();
    const items = data.items || [];
    if (items.length) {
      App.charts["chart-budget"] = new Chart(document.getElementById("chart-budget"), {
        type: "doughnut",
        data: {
          labels: items.map((b) => b.category_name),
          datasets: [{
            data: items.map((b) => parseFloat(b.spent)),
            backgroundColor: ["#3b5bdb", "#f59e0b", "#ef4444", "#12b76a", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"],
          }],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } } },
      });
    }
  },
};

function openBudgetModal(b) {
  const cats = (App.data.categories || []).filter((c) => c.active && c.type === "despesa");
  modalFormHtml({
    id: "modal-budget",
    title: b ? "Editar orçamento" : "Nova meta",
    submitText: b ? "Salvar" : "Criar",
    fieldsHtml:
      (b ? "" : fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats, b?.category_id), required: true })) +
      fieldHtml({ id: "limit_amount", label: "Limite (R$)", type: "text", value: b ? String(b.limit_amount) : "", placeholder: "0,00", required: true }) +
      fieldHtml({ id: "month", label: "Mês", type: "month", value: b?.month || App.data.budgetMonth || currentMonth() }),
    onSubmit: async (payload) => {
      payload.limit_amount = parseBrl(payload.limit_amount);
      const method = b ? "PUT" : "POST";
      const endpoint = b ? `/budgets/${b.id}` : "/budgets";
      await api(endpoint, { method, body: payload });
      toast(b ? "Orçamento atualizado" : "Orçamento criado", "success");
      App.navigate("budgets");
    },
  });
}