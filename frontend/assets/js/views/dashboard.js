/* ---------- Dashboard ---------- */

App.views.dashboard = {
  route: "dashboard",
  title: "Dashboard",
  subtitle: "Visão geral das suas finanças",
  async render() {
    const d = await api("/dashboard");
    const s = d.summary;
    const receitas = parseFloat(s.receitas_mes);
    const despesas = parseFloat(s.despesas_mes);
    const resultado = receitas - despesas;

    let recentRows = "";
    for (const t of (d.ultimas_movimentacoes || []).slice(0, 8)) {
      recentRows += `<tr>
        <td>${fmtDate(t.date)}</td>
        <td class="td-strong">${escapeHtml(t.description)}</td>
        <td>${t.category_name ? escapeHtml(t.category_name) : "—"}</td>
        <td>${typeBadge(t.type)}</td>
        <td class="text-right">${moneyCell(t.amount, t.type)}</td>
      </tr>`;
    }

    let duesHtml = "";
    for (const item of (d.proximos_vencimentos || []).slice(0, 6)) {
      const bad = item.days_left < 0;
      const lbl = item.kind === "payable" ? (bad ? "Vencida" : `em ${item.days_left}d`) : (bad ? "Vencido" : `em ${item.days_left}d`);
      duesHtml += `<div class="budget-row" style="padding:9px 0">
        <div class="budget-row__top">
          <span class="budget-row__name">${escapeHtml(item.description)}</span>
          <span class="${bad ? "amount-negative" : "text-muted"}" style="font-size:13px">${formatBRL(item.amount)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted)">
          <span>${item.kind === "payable" ? "<b>Pagar</b>" : "<b>Receber</b>"}</span><span>${fmtDate(item.due_date)} · ${lbl}</span>
        </div>
      </div>`;
    }
    if (!duesHtml) duesHtml = emptyHtml("Nada para os próximos dias");

    return `
      <div class="grid cards">
        <div class="stat stat--accent">
          <span class="stat__label">Saldo atual</span>
          <span class="stat__value">${formatBRL(s.saldo_atual)}</span>
          <span class="stat__sub">todas as contas</span>
        </div>
        <div class="stat stat--green">
          <span class="stat__label">Receitas do mês</span>
          <span class="stat__value">${formatBRL(receitas)}</span>
          <span class="stat__sub">${currentMonth()}</span>
        </div>
        <div class="stat stat--red">
          <span class="stat__label">Despesas do mês</span>
          <span class="stat__value">${formatBRL(despesas)}</span>
          <span class="stat__sub">${currentMonth()}</span>
        </div>
        <div class="stat ${resultado >= 0 ? "stat--green" : "stat--red"}">
          <span class="stat__label">Resultado do mês</span>
          <span class="stat__value">${formatBRL(resultado)}</span>
          <span class="stat__sub">${resultado >= 0 ? "superávit" : "déficit"}</span>
        </div>
      </div>

      <div class="grid two" style="margin-top:16px">
        <div class="card">
          <div class="card__head"><h3>Despesas por categoria</h3></div>
          <div class="card__body"><div class="chart-box"><canvas id="chart-categories"></canvas></div></div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Evolução mensal (6 meses)</h3></div>
          <div class="card__body"><div class="chart-box"><canvas id="chart-monthly"></canvas></div></div>
        </div>
      </div>

      <div class="grid two" style="margin-top:16px">
        <div class="card">
          <div class="card__head"><h3>Próximos vencimentos</h3></div>
          <div class="card__body">${duesHtml}</div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Últimas movimentações</h3>
            <a href="#/transactions" class="btn btn--sm btn--outline">Ver todas</a>
          </div>
          <div class="card__body table-wrap">
            <table class="data">
              <thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Tipo</th><th class="text-right">Valor</th></tr></thead>
              <tbody>${recentRows || emptyHtml()}</tbody>
            </table>
          </div>
        </div>
      </div>`;
  },
  async init() {
    const d = await api("/dashboard");
    App.charts["chart-categories"]?.destroy();
    App.charts["chart-monthly"]?.destroy();

    const cats = (d.gastos_por_categoria || []).slice(0, 8);
    if (cats.length) {
      App.charts["chart-categories"] = new Chart(document.getElementById("chart-categories"), {
        type: "doughnut",
        data: {
          labels: cats.map((c) => c.category_name || "Sem categoria"),
          datasets: [{
            data: cats.map((c) => parseFloat(c.amount)),
            backgroundColor: ["#3b5bdb", "#f59e0b", "#ef4444", "#12b76a", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"],
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
        },
      });
    }

    const months = (d.evolucao_mensal || []).map((m) => monthLabel(m.month));
    const receitasArr = (d.evolucao_mensal || []).map((m) => parseFloat(m.receitas));
    const despesasArr = (d.evolucao_mensal || []).map((m) => parseFloat(m.despesas));
    App.charts["chart-monthly"] = new Chart(document.getElementById("chart-monthly"), {
      type: "bar",
      data: {
        labels: months,
        datasets: [
          { label: "Receitas", data: receitasArr, backgroundColor: "#12b76a" },
          { label: "Despesas", data: despesasArr, backgroundColor: "#ef4444" },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
        scales: {
          x: { stacked: false },
          y: { ticks: { callback: (v) => "R$ " + Number(v).toLocaleString("pt-BR") } },
        },
      },
    });
  },
};