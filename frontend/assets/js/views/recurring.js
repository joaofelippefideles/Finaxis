/* ---------- Lançamentos recorrentes ---------- */

App.views.recurring = {
  route: "recurring",
  title: "Lançamentos recorrentes",
  subtitle: "Automatize despesas e receitas fixas",
  async render() {
    const [items, categories, accounts, cards] = await Promise.all([
      api("/recurring"),
      api("/categories"),
      api("/accounts"),
      api("/cards"),
    ]);
    App.data.categories = categories;
    App.data.accounts = accounts;
    App.data.cards = cards;

    let rows = "";
    for (const r of items || []) {
      rows += `<tr>
        <td class="td-strong">${escapeHtml(r.description)}</td>
        <td>${typeBadge(r.type)}</td>
        <td>${formatBRL(r.amount)}</td>
        <td>${ucfirst(r.frequency)}</td>
        <td>Próxima: <b>${fmtDate(r.next_due_date)}</b></td>
        <td>${r.generated_count || 0} gerado(s)</td>
        <td>${statusBadge(r.status)}</td>
        <td>
          <div class="actions-cell">
            ${r.status === "ativo" ? `<button class="btn-icon" title="Pausar" data-act="pause" data-id="${r.id}">${icon("pause")}</button>` : ""}
            ${r.status === "pausado" ? `<button class="btn-icon" title="Ativar" data-act="resume" data-id="${r.id}">${icon("play")}</button>` : ""}
            ${r.status === "ativo" ? `<button class="btn-icon" title="Cancelar" data-act="cancel" data-id="${r.id}">${icon("x")}</button>` : ""}
            <button class="btn-icon" title="Editar" data-act="edit" data-id="${r.id}">${icon("edit-2")}</button>
            <button class="btn-icon danger" title="Excluir" data-act="del" data-id="${r.id}">${icon("trash-2")}</button>
          </div>
        </td>
      </tr>`;
    }
    return `
      <div style="display:flex;justify-content:flex-end;gap:10px;margin-bottom:16px">
        <button class="btn btn--green" id="btn-process">${icon("play")} Gerar lançamentos agora</button>
        <button class="btn" id="btn-new-recurring">${icon("plus")} Nova recorrência</button>
      </div>
      <div class="card">
        <div class="card__head"><h3>Recorrências</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Descrição</th><th>Tipo</th><th>Valor</th><th>Frequência</th><th>Próximo vencimento</th><th>Gerados</th><th>Status</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="8">${emptyHtml("Nenhuma recorrência cadastrada")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    document.getElementById("btn-new-recurring")?.addEventListener("click", () => openRecurringModal());
    document.getElementById("btn-process")?.addEventListener("click", async () => {
      try {
        const res = await api("/recurring/process", { method: "POST" });
        toast(`${res.generated} lançamentos gerados`, "success");
        App.navigate("recurring");
      } catch (err) { toast(err.message, "error"); }
    });
    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        const items = await api("/recurring");
        const r = items.find((x) => x.id === id);
        if (!r) return;
        if (act === "pause") {
          await api(`/recurring/${id}`, { method: "PUT", body: { status: "pausado" } });
          App.navigate("recurring");
        } else if (act === "resume") {
          await api(`/recurring/${id}`, { method: "PUT", body: { status: "ativo" } });
          App.navigate("recurring");
        } else if (act === "cancel") {
          confirmDialog("Cancelar esta recorrência?", async () => {
            await api(`/recurring/${id}`, { method: "PUT", body: { status: "cancelado" } });
            toast("Recorrência cancelada", "success");
            App.navigate("recurring");
          });
        } else if (act === "del") {
          confirmDialog("Excluir esta recorrência?", async () => {
            try {
              await api(`/recurring/${id}`, { method: "DELETE" });
              toast("Recorrência excluída", "success");
              App.navigate("recurring");
            } catch (err) { toast(err.message, "error"); }
          });
        } else if (act === "edit") {
          openRecurringModal(r);
        }
      });
    });
  },
};

function openRecurringModal(r) {
  const cats = (App.data.categories || []).filter((c) => c.active);
  const accs = (App.data.accounts || []).filter((a) => a.active);
  const cards = (App.data.cards || []).filter((c) => c.status === "ativo");
  const freq = ["diario", "semanal", "mensal", "anual"];
  modalFormHtml({
    id: "modal-recurring",
    title: r ? "Editar recorrência" : "Nova recorrência",
    size: "modal--lg",
    submitText: r ? "Salvar" : "Criar",
    fieldsHtml:
      fieldHtml({ id: "description", label: "Descrição", value: r?.description || "", required: true, span2: true }) +
      fieldHtml({ id: "type", label: "Tipo", type: "select", options: ["receita", "despesa"].map((t) => `<option value="${t}" ${r?.type === t ? "selected" : ""}>${ucfirst(t)}</option>`).join(""), required: true }) +
      fieldHtml({ id: "amount", label: "Valor (R$)", type: "text", value: r ? String(r.amount) : "", placeholder: "0,00", required: true }) +
      fieldHtml({ id: "frequency", label: "Frequência", type: "select", options: freq.map((f) => `<option value="${f}" ${r?.frequency === f ? "selected" : ""}>${ucfirst(f)}</option>`).join(""), required: true }) +
      fieldHtml({ id: "start_date", label: "Início", type: "date", value: r?.start_date || todayISO(), required: true }) +
      fieldHtml({ id: "end_date", label: "Fim (opcional)", type: "date", value: r?.end_date || "" }) +
      fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats, r?.category_id) }) +
      fieldHtml({ id: "account_id", label: "Conta", type: "select", options: optionsHtml(accs, r?.account_id) }) +
      fieldHtml({ id: "card_id", label: "Cartão", type: "select", options: optionsHtml(cards, r?.card_id), span2: true }),
    onSubmit: async (payload) => {
      for (const f of ["category_id", "account_id", "card_id", "end_date"]) {
        if (!payload[f]) delete payload[f];
      }
      payload.amount = parseBrl(payload.amount);
      const method = r ? "PUT" : "POST";
      const endpoint = r ? `/recurring/${r.id}` : "/recurring";
      await api(endpoint, { method, body: payload });
      toast(r ? "Recorrência atualizada" : "Recorrência criada", "success");
      App.navigate("recurring");
    },
  });
}