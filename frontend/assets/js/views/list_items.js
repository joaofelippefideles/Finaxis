/* ---------- Compartilhado: contas a pagar/receber ---------- */

function openListItemModal(kind) {
  const isPayable = kind === "payables";
  const cats = (App.data.categories || []).filter((c) => c.active && c.type === (isPayable ? "despesa" : "receita"));
  const accs = (App.data.accounts || []).filter((a) => a.active);
  const freq = ["mensal", "semanal", "anual", "diario"];
  modalFormHtml({
    id: "modal-list-item",
    title: isPayable ? "Nova conta a pagar" : "Nova conta a receber",
    submitText: "Criar",
    fieldsHtml:
      fieldHtml({ id: "description", label: "Descrição", required: true, span2: true }) +
      fieldHtml({ id: "amount", label: "Valor (R$)", type: "text", placeholder: "0,00", required: true }) +
      fieldHtml({ id: "due_date", label: "Vencimento", type: "date", value: todayISO(), required: true }) +
      fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats) }) +
      fieldHtml({ id: "account_id", label: "Conta", type: "select", options: optionsHtml(accs) }) +
      fieldHtml({ id: "frequency", label: "Repetir (após quitar)", type: "select", options: `<option value="">Não repetir</option>` + freq.map((f) => `<option value="${f}">${ucfirst(f)}</option>`).join("") }) +
      fieldHtml({ id: "observation", label: "Observação", type: "textarea", span2: true }),
    onSubmit: async (payload) => {
      for (const f of ["category_id", "account_id", "frequency"]) {
        if (!payload[f]) delete payload[f];
      }
      payload.amount = parseBrl(payload.amount);
      await api(`/${kind}`, { method: "POST", body: payload });
      toast(isPayable ? "Conta a pagar criada" : "Conta a receber criada", "success");
      App.navigate(kind);
    },
  });
}

function bindListItemActions(kind) {
  const isPayable = kind === "payables";
  document.querySelectorAll("button[data-act]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const { act, id } = btn.dataset;
      const items = isPayable ? App.data.payables || [] : App.data.receivables || [];
      const item = items.find?.((x) => x.id === id);
      if (act === "pay" || act === "receive") {
        const verb = isPayable ? "quitar" : "receber";
        confirmDialog(`Confirmar ${verb === "quitar" ? "pagamento" : "recebimento"} de ${item?.description ? `"${item.description}"` : "este item"}?${isPayable ? "" : ""}`, async () => {
          try {
            await api(`/${kind}/${id}/${isPayable ? "pay" : "receive"}`, { method: "POST" });
            toast(`${ucfirst(verb)} realizado`, "success");
            App.navigate(kind);
          } catch (err) { toast(err.message, "error"); }
        });
      } else if (act === "reopen") {
        try {
          await api(`/${kind}/${id}/reopen`, { method: "POST" });
          toast(`${isPayable ? "Conta" : "Conta"} reaberta`, "success");
          App.navigate(kind);
        } catch (err) { toast(err.message, "error"); }
      } else if (act === "cancel") {
        confirmDialog("Cancelar este item?", async () => {
          try {
            await api(`/${kind}/${id}/cancel`, { method: "POST" });
            toast("Item cancelado", "success");
            App.navigate(kind);
          } catch (err) { toast(err.message, "error"); }
        });
      } else if (act === "del") {
        confirmDialog("Excluir este item?", async () => {
          try {
            await api(`/${kind}/${id}`, { method: "DELETE" });
            toast("Item excluído", "success");
            App.navigate(kind);
          } catch (err) { toast(err.message, "error"); }
        });
      } else if (act === "edit") {
        bindListItemActions.cached = items;
        const item = items.find((x) => x.id === id);
        if (item) openListItemEditModal(kind, item);
      }
    });
  });
}

function openListItemEditModal(kind, item) {
  const isPayable = kind === "payables";
  const cats = (App.data.categories || []).filter((c) => c.active && c.type === (isPayable ? "despesa" : "receita"));
  const accs = (App.data.accounts || []).filter((a) => a.active);
  const freq = ["mensal", "semanal", "anual", "diario"];
  modalFormHtml({
    id: "modal-list-item",
    title: isPayable ? "Editar conta a pagar" : "Editar conta a receber",
    submitText: "Salvar",
    fieldsHtml:
      fieldHtml({ id: "description", label: "Descrição", value: item.description, required: true, span2: true }) +
      fieldHtml({ id: "amount", label: "Valor (R$)", type: "text", value: String(item.amount), required: true }) +
      fieldHtml({ id: "due_date", label: "Vencimento", type: "date", value: item.due_date, required: true }) +
      fieldHtml({ id: "category_id", label: "Categoria", type: "select", options: optionsHtml(cats, item.category_id) }) +
      fieldHtml({ id: "account_id", label: "Conta", type: "select", options: optionsHtml(accs, item.account_id) }) +
      fieldHtml({ id: "frequency", label: "Repetir", type: "select", options: `<option value="">Não repetir</option>` + freq.map((f) => `<option value="${f}" ${item.frequency === f ? "selected" : ""}>${ucfirst(f)}</option>`).join("") }) +
      fieldHtml({ id: "observation", label: "Observação", type: "textarea", value: item.observation || "", span2: true }),
    onSubmit: async (payload) => {
      for (const f of ["category_id", "account_id", "frequency"]) {
        if (!payload[f]) delete payload[f];
      }
      payload.amount = parseBrl(payload.amount);
      await api(`/${kind}/${item.id}`, { method: "PUT", body: payload });
      toast("Item atualizado", "success");
      App.navigate(kind);
    },
  });
}