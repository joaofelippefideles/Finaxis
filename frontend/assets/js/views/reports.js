/* ---------- Relatórios ---------- */

App.views.reports = {
  route: "reports",
  title: "Relatórios",
  subtitle: "Análises e exportação",
  async render() {
    const [categories, accounts, cards] = await Promise.all([
      api("/categories"),
      api("/accounts"),
      api("/cards"),
    ]);
    App.data.categories = categories;
    App.data.accounts = accounts;
    App.data.cards = cards;

    const today = new Date();
    const start = monthsBack(11);
    const end = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

    return `
      <div class="card">
        <div class="card__body">
          <form id="report-filters" class="form-grid">
            ${fieldHtml({ id: "start_date", label: "De", type: "date", value: start + "-01", required: true })}
            ${fieldHtml({ id: "end_date", label: "Até", type: "date", value: end, required: true })}
            ${fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(categories) })}
            ${fieldHtml({ id: "account_id", label: "Conta", type: "select", options: optionsHtml(accounts) })}
            ${fieldHtml({ id: "card_id", label: "Cartão", type: "select", options: optionsHtml(cards) })}
            <div class="field">
              <label>Filtros</label>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button class="btn" type="submit">${icon("search")} Gerar relatório</button>
                <button class="btn btn--outline" type="button" data-export="csv">CSV</button>
                <button class="btn btn--outline" type="button" data-export="xlsx">XLSX</button>
                <button class="btn btn--outline" type="button" data-export="pdf">PDF</button>
              </div>
            </div>
          </form>
        </div>
      </div>
      <div id="report-results" style="margin-top:16px">${emptyHtml("Defina o período e clique em Gerar relatório")}</div>`;
  },
  init() {
    const form = document.getElementById("report-filters");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      const query = {
        start_date: payload.start_date,
        end_date: payload.end_date,
        category_id: payload.category_id || undefined,
        account_id: payload.account_id || undefined,
        card_id: payload.card_id || undefined,
      };
      try {
        const report = await api("/reports/summary", { query });
        renderReportResults(report);
      } catch (err) {
        toast(err.message, "error");
      }
    });

    form.querySelectorAll("[data-export]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const fd = new FormData(form);
        const payload = Object.fromEntries(fd.entries());
        const query = {
          fmt: btn.dataset.export,
          start_date: payload.start_date,
          end_date: payload.end_date,
          category_id: payload.category_id || undefined,
          account_id: payload.account_id || undefined,
          card_id: payload.card_id || undefined,
        };
        try {
          btn.disabled = true;
          await apiDownload("/reports/export", { query });
        } catch (err) {
          toast(err.message, "error");
        } finally {
          btn.disabled = false;
        }
      });
    });
  },
};

async function renderReportResults(report) {
  const q = report.query || {};
  const totalRec = parseFloat(report.total_receitas || 0);
  const totalDesp = parseFloat(report.total_despesas || 0);
  const resultado = totalRec - totalDesp;

  const catRows = (report.por_categoria || []).map((c) => `
    <tr><td>${escapeHtml(c.category_name || "Sem categoria")}</td><td class="text-right">${formatBRL(c.amount)}</td>
    <td><div class="progress"><div style="width:${Math.min(100, ((parseFloat(c.amount) || 0) / (totalDesp || 1)) * 100)}%"></div></div></td></tr>`).join("");

  const flowRows = (report.fluxo_caixa || []).map((f) => `
    <tr><td>${fmtDate(f.date)}</td><td class="td-strong">${escapeHtml(f.description || "—")}</td>
    <td class="text-right">${formatBRL(f.value)}</td><td>${typeBadge(f.type)}</td></tr>`).join("");

  const txnRows = (report.lancamentos || []).map((t) => `
    <tr><td>${t.date ? fmtDate(t.date) : "—"}</td><td class="td-strong">${escapeHtml(t.description || "—")}</td>
    <td>${escapeHtml(t.category_name || t.category || "—")}</td>
    <td class="text-right">${moneyCell(t.amount, t.type)}</td><td>${statusBadge(t.status)}</td></tr>`).join("");

  const container = document.getElementById("report-results");
  container.innerHTML = `
    <div class="grid cards">
      <div class="stat stat--green"><span class="stat__label">Receitas</span><span class="stat__value">${formatBRL(totalRec)}</span><span class="stat__sub">${fmtDate(q.start_date)} a ${fmtDate(q.end_date)}</span></div>
      <div class="stat stat--red"><span class="stat__label">Despesas</span><span class="stat__value">${formatBRL(totalDesp)}</span></div>
      <div class="stat ${resultado >= 0 ? "stat--green" : "stat--red"}"><span class="stat__label">Resultado</span><span class="stat__value">${formatBRL(resultado)}</span></div>
      <div class="stat stat--accent"><span class="stat__label">Categorias</span><span class="stat__value">${(report.por_categoria || []).length}</span><span class="stat__sub">${(report.lancamentos || []).length} lançamentos</span></div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="card__head"><h3>Evolução mensal</h3></div>
      <div class="card__body"><div class="chart-box"><canvas id="chart-report"></canvas></div></div>
    </div>
    <div class="grid two" style="margin-top:16px">
      <div class="card">
        <div class="card__head"><h3>Por categoria</h3></div>
        <div class="card__body table-wrap">
          <table class="data"><thead><tr><th>Categoria</th><th class="text-right">Valor</th><th></th></tr></thead>
          <tbody>${catRows || `<tr><td colspan="3">${emptyHtml()}</td></tr>`}</tbody></table>
        </div>
      </div>
      <div class="card">
        <div class="card__head"><h3>Fluxo de caixa</h3></div>
        <div class="card__body table-wrap">
          <table class="data"><thead><tr><th>Data</th><th>Descrição</th><th class="text-right">Valor</th><th>Tipo</th></tr></thead>
          <tbody>${flowRows || `<tr><td colspan="4">${emptyHtml()}</td></tr>`}</tbody></table>
        </div>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="card__head"><h3>Lançamentos</h3></div>
      <div class="card__body table-wrap">
        <table class="data"><thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th class="text-right">Valor</th><th>Status</th></tr></thead>
        <tbody>${txnRows || `<tr><td colspan="5">${emptyHtml()}</td></tr>`}</tbody></table>
      </div>
    </div>`;

  App.charts["chart-report"]?.destroy();
  const months = (report.evolucao_mensal || []).map((m) => monthLabel(m.month));
  App.charts["chart-report"] = new Chart(document.getElementById("chart-report"), {
    type: "bar",
    data: {
      labels: months,
      datasets: [
        { label: "Receitas", data: (report.evolucao_mensal || []).map((m) => parseFloat(m.receitas)), backgroundColor: "#12b76a" },
        { label: "Despesas", data: (report.evolucao_mensal || []).map((m) => parseFloat(m.despesas)), backgroundColor: "#ef4444" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
      scales: { y: { ticks: { callback: (v) => "R$ " + Number(v).toLocaleString("pt-BR") } } },
    },
  });
}