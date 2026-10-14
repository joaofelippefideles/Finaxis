/* ---------- Categorias ---------- */

App.views.categories = {
  route: "categories",
  title: "Categorias",
  subtitle: "Organize receitas e despesas",
  async render() {
    const type = App.data.catType || "despesa";
    const categories = await api("/categories", { query: { type } });
    App.data.categoriesAll = await api("/categories");

    let rows = "";
    for (const c of categories || []) {
      const dots = c.color || "#64748b";
      rows += `<tr>
        <td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${dots};margin-right:8px"></span>${escapeHtml(c.name)}</td>
        <td>${typeBadge(c.type)}</td>
        <td>${c.is_default ? '<span class="badge badge--blue">Padrão</span>' : "—"}</td>
        <td>${c.active ? '<span class="badge badge--green">Ativa</span>' : '<span class="badge badge--gray">Inativa</span>'}</td>
        <td>
          <div class="actions-cell">
            <button class="btn-icon" title="Editar" data-act="edit" data-id="${c.id}">${icon("edit-2")}</button>
            <button class="btn-icon" title="Ativar/Inativar" data-act="toggle" data-id="${c.id}" data-active="${c.active}">${icon(c.active ? "toggle-left" : "toggle-right")}</button>
            ${c.is_default ? "" : `<button class="btn-icon danger" title="Excluir" data-act="del" data-id="${c.id}">${icon("trash-2")}</button>`}
          </div>
        </td>
      </tr>`;
    }

    return `
      <div class="card">
        <div class="card__head">
          <div class="tabs" style="margin:0;border:none">
            <button class="tab ${type === "despesa" ? "active" : ""}" data-t="despesa">Despesas</button>
            <button class="tab ${type === "receita" ? "active" : ""}" data-t="receita">Receitas</button>
          </div>
          <button class="btn" id="btn-new-category">${icon("plus")} Nova categoria</button>
        </div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead><tr><th>Nome</th><th>Tipo</th><th>Origem</th><th>Status</th><th></th></tr></thead>
            <tbody>${rows || `<tr><td colspan="5">${emptyHtml("Nenhuma categoria")}</td></tr>`}</tbody>
          </table>
        </div>
      </div>`;
  },
  init() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        App.data.catType = tab.dataset.t;
        App.navigate("categories");
      });
    });
    document.getElementById("btn-new-category")?.addEventListener("click", () => openCategoryModal());
    document.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const { act, id } = btn.dataset;
        const type = App.data.catType || "despesa";
        const cats = await api("/categories", { query: { type } });
        const c = cats.find((x) => x.id === id);
        if (act === "edit") {
          openCategoryModal(c);
        } else if (act === "toggle") {
          await api(`/categories/${id}/toggle?active=${btn.dataset.active === "true" ? "false" : "true"}`, { method: "PATCH" });
          toast("Status atualizado", "success");
          App.navigate("categories");
        } else if (act === "del") {
          confirmDialog(`Excluir a categoria "${c.name}"?`, async () => {
            try {
              await api(`/categories/${id}`, { method: "DELETE" });
              toast("Categoria excluída", "success");
              App.navigate("categories");
            } catch (err) { toast(err.message, "error"); }
          });
        }
      });
    });
  },
};

function openCategoryModal(c) {
  modalFormHtml({
    id: "modal-category",
    title: c ? "Editar categoria" : "Nova categoria",
    submitText: c ? "Salvar" : "Criar",
    fieldsHtml:
      (c ? "" : fieldHtml({ id: "type", label: "Tipo", type: "select", options: `<option value="despesa" ${App.data.catType !== "receita" ? "selected" : ""}>Despesa</option><option value="receita" ${App.data.catType === "receita" ? "selected" : ""}>Receita</option>`, required: true })) +
      fieldHtml({ id: "name", label: "Nome", value: c?.name || "", placeholder: "Ex.: Moradia", required: true }) +
      fieldHtml({ id: "color", label: "Cor (hex)", value: c?.color || "#3b5bdb", placeholder: "#3b5bdb" }) +
      fieldHtml({ id: "icon", label: "Ícone", value: c?.icon || "", placeholder: "Ex.: home" }),
    onSubmit: async (payload) => {
      if (!payload.color) delete payload.color;
      if (!payload.icon) delete payload.icon;
      const method = c ? "PUT" : "POST";
      const endpoint = c ? `/categories/${c.id}` : "/categories";
      await api(endpoint, { method, body: payload });
      toast(c ? "Categoria atualizada" : "Categoria criada", "success");
      App.navigate("categories");
    },
  });
}