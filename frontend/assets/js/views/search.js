/* ---------- Busca global ---------- */

App.views.search = {
  route: "search",
  title: "Busca",
  subtitle: "Resultados da pesquisa",
  async render() {
    const q = new URLSearchParams(location.hash.split("?")[1] || "");
    const query = q.get("q") || "";
    const res = query ? await api("/search", { query: { q: query, page_size: 50 } }) : null;

    if (!query) return `<div class="card"><div class="card__body">${emptyHtml("Digite algo para pesquisar")}</div></div>`;

    let rows = "";
    for (const r of res.results || []) {
      rows += `<tr>
        <td>${fmtDate(r.date)}</td>
        <td class="td-strong">${escapeHtml(r.description)}</td>
        <td>${escapeHtml(r.category || "—")}</td>
        <td>${typeBadge(r.type)}</td>
        <td>${statusBadge(r.status)}</td>
        <td class="text-right">${moneyCell(r.amount, r.type)}</td>
      </tr>`;
    }
    return `
      <div class="card">
        <div class="card__head"><h3>Resultados para "${escapeHtml(query)}" · ${res?.total ?? 0} encontrado(s)</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Tipo</th><th>Status</th><th class="text-right">Valor</th></tr></thead>
            <tbody>${rows || `<tr><td colspan="6">${emptyHtml("Nada encontrado")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {},
};