/* ---------- Compras parceladas ---------- */

App.views.installments = {
  route: "installments",
  title: "Compras parceladas",
  subtitle: "Parcelas geradas automaticamente",
  async render() {
    const [installments, categories, cards] = await Promise.all([
      api("/installments"),
      api("/categories"),
      api("/cards"),
    ]);
    App.data.categories = categories;
    App.data.cards = cards;

    let rows = "";
    for (const gi of installments || []) {
      const pct = gi.installments_total > 0 ? Math.round((gi.paid_count / gi.installments_total) * 100) : 0;
      const barCls = gi.status === "concluido" ? "" : gi.status === "cancelado" ? "critical" : "";
      rows += `<tr>
        <td class="td-strong">${escapeHtml(gi.description)}</td>
        <td>${fmtDate(gi.first_due_date)}</td>
        <td>${formatBRL(gi.total_value)}</td>
        <td>${gi.paid_count}/${gi.installments_total}</td>
        <td style="min-width:140px">
          <div class="progress ${barCls}"><div style="width:${pct}%"></div></div>
        </td>
        <td>${statusBadge(gi.status)}</td>
        <td>
          <div class="actions-cell">
            <button class="btn-icon" title="Ver parcelas" data-act="view" data-id="${gi.id}">${icon("eye")}</button>
            <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${gi.id}">${icon("trash-2")}</button>
          </div>
        </td>
      </tr>`;
    }
    return `
      <div class="card">
        <div class="card__head"><h3>Parcelamentos</h3><button class="btn" id="btn-new-installer">${icon("plus")} Nova compra parcelada</button></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Descrição</th><th>Início</th><th>Valor total</th><th>Parcelas</th><th>Progresso</th><th>Status</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="7">${emptyHtml("Nenhuma compra parcelada")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    document.getElementById("btn-new-installer")?.addEventListener("click", () => openInstallmentModal());
    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        if (act === "del") {
          confirmDialog("Excluir este parcelamento? Todas as parcelas serão removidas.", async () => {
            try {
              await api(`/installments/${id}`, { method: "DELETE" });
              toast("Parcelamento excluído", "success");
              App.navigate("installments");
            } catch (err) { toast(err.message, "error"); }
          });
        } else if (act === "view") {
          const gi = (await api("/installments")).find((x) => x.id === id);
          if (!gi) return;
          let rows = "";
          for (const p of gi.parcels || []) {
            rows += `<tr>
              <td>${fmtDate(p.date)}</td>
              <td>${escapeHtml(p.description)}</td>
              <td class="text-right">${formatBRL(p.amount)}</td>
              <td>${statusBadge(p.status)}</td>
              <td>${p.status === "pendente" ? `<button class="btn btn--sm btn--outline" data-pay-parcel="${p.id}">Pagou?</button>` : ""}</td>
            </tr>`;
          }
          App.showModal({
            title: `${escapeHtml(gi.description)} · parcelas`,
            size: "modal--lg",
            body: `<div style="display:flex;gap:18px;margin-bottom:14px;flex-wrap:wrap">
              <div><span class="text-muted">Total</span><div class="td-strong">${formatBRL(gi.total_value)}</div></div>
              <div><span class="text-muted">Valor por parcela</span><div class="td-strong">${gi.parcels.length ? formatBRL(gi.parcels[0].amount) : "—"}</div></div>
              <div><span class="text-muted">Status</span><div>${statusBadge(gi.status)}</div></div>
            </div>
            <div class="table-wrap">
              <table class="data">
                <thead><tr><th>Vencimento</th><th>Descrição</th><th class="text-right">Valor</th><th>Status</th><th></th></tr></thead>
                <tbody>${rows || `<tr><td colspan="5">${emptyHtml()}</td></tr>`}</tbody>
              </table>
            </div>`,
          });
        }
      });
    });
    document.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-pay-parcel]");
      if (!btn) return;
      const tid = btn.dataset.payParcel;
      try {
        await api(`/transactions/${tid}/pay`, { method: "POST" });
        toast("Parcela marcada como paga", "success");
        App.navigate("installments");
      } catch (err) { toast(err.message, "error"); }
    }, { once: false });
  },
};

function openInstallmentModal() {
  const cats = (App.data.categories || []).filter((c) => c.active && c.type === "despesa");
  const cards = (App.data.cards || []).filter((c) => c.status === "ativo");
  modalFormHtml({
    id: "modal-installer",
    title: "Nova compra parcelada",
    submitText: "Criar",
    fieldsHtml:
      fieldHtml({ id: "description", label: "Descrição", required: true, span2: true }) +
      fieldHtml({ id: "total_value", label: "Valor total (R$)", type: "text", placeholder: "0,00", required: true }) +
      fieldHtml({ id: "installments_total", label: "Quantidade de parcelas", type: "number", min: 2, max: 120, required: true }) +
      fieldHtml({ id: "first_due_date", label: "Primeira parcela", type: "date", value: todayISO(), required: true }) +
      fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats) }) +
      fieldHtml({ id: "card_id", label: "Cartão", type: "select", options: optionsHtml(cards), required: true }) +
      fieldHtml({ id: "observation", label: "Observação", type: "textarea", span2: true }),
    onSubmit: async (payload) => {
      if (!payload.category_id) delete payload.category_id;
      payload.total_value = parseBrl(payload.total_value);
      payload.installments_total = Number(payload.installments_total);
      await api("/installments", { method: "POST", body: payload });
      toast("Compra parcelada criada", "success");
      App.navigate("installments");
    },
  });
}