/* ---------- Cartões de crédito ---------- */

App.views.cards = {
  route: "cards",
  title: "Cartões de crédito",
  subtitle: "Limites, faturas e vencimentos",
  async render() {
    const [cards, accounts] = await Promise.all([api("/cards"), api("/accounts")]);
    App.data.cards = cards;
    App.data.accounts = accounts;

    let cardsHtml = "";
    for (const c of cards || []) {
      const used = parseFloat(c.used_limit);
      const limit = parseFloat(c.limit_amount);
      const pct = limit > 0 ? Math.round((used / limit) * 100) : 0;
      const barCls = pct >= 80 ? "critical" : pct >= 60 ? "warn" : "";
      cardsHtml += `
        <div class="card">
          <div class="card__body">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div>
                <div class="td-strong" style="font-size:15px">${escapeHtml(c.name)}</div>
                <div class="text-muted" style="font-size:12px">${escapeHtml(c.bank || "Cartão")} · fecha dia ${c.closing_day} · vence dia ${c.due_day}</div>
              </div>
              ${statusBadge(c.status)}
            </div>
            <div style="margin-top:12px">
              <div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:5px">
                <span>Limite: ${formatBRL(c.limit_amount)}</span>
                <span>Disponível: <b class="${used > limit ? "amount-negative" : ""}">${formatBRL(c.available_limit)}</b></span>
              </div>
              <div class="progress ${barCls}"><div style="width:${pct}%"></div></div>
              <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:11.5px;color:var(--text-muted)">
                <span>uso ${pct}%</span>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px">
              <div class="stat" style="padding:10px 12px;box-shadow:none">
                <span class="stat__label">Fatura atual</span>
                <span class="stat__value" style="font-size:16px">${formatBRL(c.current_invoice)}</span>
              </div>
              <div class="stat" style="padding:10px 12px;box-shadow:none">
                <span class="stat__label">Próxima</span>
                <span class="stat__value" style="font-size:16px">${formatBRL(c.next_invoice)}</span>
              </div>
            </div>
            <div style="display:flex;gap:8px;margin-top:12px">
              <button class="btn btn--sm btn--outline" data-card-act="invoices" data-id="${c.id}">${icon("file-text")} Faturas</button>
              <button class="btn btn--sm btn--outline" data-card-act="edit" data-id="${c.id}">${icon("edit-2")} Editar</button>
              <button class="btn btn--sm btn--ghost danger" data-card-act="del" data-id="${c.id}">${icon("trash-2")}</button>
            </div>
          </div>
        </div>`;
    }

    return `
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn" id="btn-new-card">${icon("plus")} Novo cartão</button>
      </div>
      <div class="grid three">${cardsHtml || `<div class="card"><div class="card__body">${emptyHtml("Nenhum cartão cadastrado")}</div></div>`}</div>`;
  },
  init() {
    document.getElementById("btn-new-card")?.addEventListener("click", () => openCardModal());
    document.querySelectorAll("button[data-card-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { cardAct, id } = btn.dataset;
        const card = (App.data.cards || []).find((c) => c.id === id);
        if (cardAct === "edit") {
          openCardModal(card);
        } else if (cardAct === "del") {
          confirmDialog(`Excluir o cartão "${card.name}"?`, async () => {
            try {
              await api(`/cards/${id}`, { method: "DELETE" });
              toast("Cartão excluído", "success");
              App.navigate("cards");
            } catch (err) { toast(err.message, "error"); }
          });
        } else if (cardAct === "invoices") {
          showInvoices(id, card?.name);
        }
      });
    });
  },
};

function openCardModal(card) {
  const accounts = (App.data.accounts || []).filter((a) => a.active);
  const opts = optionsHtml(accounts, card?.account_id);
  const statuses = ["ativo", "bloqueado", "cancelado"];
  modalFormHtml({
    id: "modal-card",
    title: card ? "Editar cartão" : "Novo cartão",
    submitText: card ? "Salvar" : "Criar",
    fieldsHtml:
      fieldHtml({ id: "name", label: "Nome", value: card?.name || "", placeholder: "Ex.: Visa Platinum", required: true, span2: true }) +
      fieldHtml({ id: "bank", label: "Banco", value: card?.bank || "" }) +
      fieldHtml({ id: "limit_amount", label: "Limite (R$)", value: card ? String(card.limit_amount) : "0", placeholder: "0,00" }) +
      fieldHtml({ id: "closing_day", label: "Dia de fechamento", type: "number", value: card?.closing_day || 1, min: 1, max: 31 }) +
      fieldHtml({ id: "due_day", label: "Dia de vencimento", type: "number", value: card?.due_day || 10, min: 1, max: 31 }) +
      fieldHtml({ id: "account_id", label: "Conta para fatura", type: "select", options: opts }) +
      fieldHtml({ id: "status", label: "Status", type: "select", options: statuses.map((s) => `<option value="${s}" ${card?.status === s ? "selected" : ""}>${ucfirst(s)}</option>`).join(""), span2: true }),
    onSubmit: async (payload) => {
      if (!payload.account_id) delete payload.account_id;
      payload.limit_amount = parseBrl(payload.limit_amount);
      payload.closing_day = Number(payload.closing_day);
      payload.due_day = Number(payload.due_day);
      const method = card ? "PUT" : "POST";
      const endpoint = card ? `/cards/${card.id}` : "/cards";
      await api(endpoint, { method, body: payload });
      toast(card ? "Cartão atualizado" : "Cartão criado", "success");
      App.navigate("cards");
    },
  });
}

async function showInvoices(cardId, cardName) {
  const invoices = await api(`/cards/${cardId}/invoices`);
  let html = `<div class="tabs">`;
  for (const inv of invoices) {
    html += `<button class="tab ${inv.month === currentMonth() ? "active" : ""}" data-inv="${inv.month}" data-card="${cardId}">${monthLabel(inv.month)}</button>`;
  }
  html += `</div>`;
  const active = invoices.find((i) => i.month === currentMonth()) || invoices[invoices.length - 1];
  html += renderInvoice(cardId, cardName, active);
  App.showModal({
    title: `Faturas · ${escapeHtml(cardName || "")}`,
    size: "modal--lg",
    body: html,
  });

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", async () => {
      const inv = (await api(`/cards/${cardId}/invoices`)).find((i) => i.month === tab.dataset.inv);
      document.querySelector("[data-modal-body]").innerHTML = renderInvoice(cardId, cardName, inv);
      const allTabs = document.querySelectorAll(".tab");
      allTabs.forEach((t) => t.classList.toggle("active", t === tab));
    });
  });
}

function renderInvoice(cardId, cardName, inv) {
  if (!inv) return emptyHtml("Sem faturas");
  let rows = "";
  for (const it of inv.items || []) {
    const lbl = it.installment_number ? `${it.description} (${it.installment_number}/${it.installments_total})` : it.description;
    rows += `<tr><td>${fmtDate(it.date)}</td><td>${escapeHtml(lbl)}</td><td class="text-right">${formatBRL(it.amount)}</td></tr>`;
  }
  const canPay = !!inv.items?.length;
  return `
    <div data-modal-body>
      <div class="card">
        <div class="card__body">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
            <div>
              <div class="text-muted">Fatura ${monthLabel(inv.month)} · vence ${fmtDate(inv.due_date)}</div>
              <div class="stat__value">${formatBRL(inv.total)}</div>
            </div>
            ${canPay ? `<button class="btn btn--green" id="btn-pay-invoice" data-card="${cardId}" data-month="${inv.month}" data-total="${inv.total}">${icon("credit-card")} Pagar fatura</button>` : ""}
          </div>
          <div class="table-wrap" style="margin-top:14px">
            <table class="data">
              <thead><tr><th>Data</th><th>Compra</th><th class="text-right">Valor</th></tr></thead>
              <tbody>${rows || `<tr><td colspan="3">${emptyHtml("Fatura sem lançamentos")}</td></tr>`}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>`;
}

App.showModal = function ({ title, body, size = "" }) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay open";
  overlay.innerHTML = `
    <div class="modal ${size}">
      <div class="modal__head"><h3>${title}</h3><button class="btn-icon" data-modal-close>✕</button></div>
      <div class="modal__body">${body}</div>
    </div>`;
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  overlay.querySelectorAll("[data-modal-close]").forEach((b) => b.addEventListener("click", () => overlay.remove()));
  document.body.appendChild(overlay);
};

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("#btn-pay-invoice");
  if (!btn) return;
  const { card, month, total } = btn.dataset;
  confirmDialog(`Pagar a fatura de ${monthLabel(month)} no valor de ${formatBRL(total)}? A conta vinculada ao cartão será usada.`, async () => {
    try {
      const res = await api(`/cards/${card}/invoices/${month}/pay`, { method: "POST" });
      toast(`Fatura paga: ${formatBRL(res.paid_total)}`, "success");
      App.navigate("cards");
    } catch (err) { toast(err.message, "error"); }
  }, "Pagar fatura");
});