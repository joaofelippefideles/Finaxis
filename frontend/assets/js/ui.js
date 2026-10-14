/* ---------- Componentes de UI ---------- */

function toast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast toast--${type}`;
  el.innerHTML = `<span>${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transition = "opacity .3s";
    setTimeout(() => el.remove(), 320);
  }, 3200);
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

function confirmDialog(message, onYes, title = "Confirmar") {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay open";
  overlay.innerHTML = `
    <div class="modal modal--sm">
      <div class="modal__head"><h3>${escapeHtml(title)}</h3></div>
      <div class="modal__body"><p style="margin:0">${escapeHtml(message)}</p></div>
      <div class="modal__foot">
        <button class="btn btn--ghost" data-confirm-no>Cancelar</button>
        <button class="btn btn--danger" data-confirm-yes>Confirmar</button>
      </div>
    </div>`;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });
  overlay.querySelector("[data-confirm-no]").addEventListener("click", () => overlay.remove());
  overlay.querySelector("[data-confirm-yes]").addEventListener("click", () => {
    overlay.remove();
    onYes();
  });
  document.body.appendChild(overlay);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function loadingHtml(text = "Carregando...") {
  return `<div class="loading"><div class="spinner"></div><span>${escapeHtml(text)}</span></div>`;
}

function emptyHtml(text = "Nenhum registro encontrado") {
  return `<div class="empty-state"><div class="empty-icon">•</div><p>${escapeHtml(text)}</p></div>`;
}

function statusBadge(status) {
  const map = {
    pendente: ["badge--amber", "Pendente"],
    pago: ["badge--green", "Pago"],
    recebido: ["badge--green", "Recebido"],
    cancelado: ["badge--gray", "Cancelado"],
    ativo: ["badge--green", "Ativo"],
    pausado: ["badge--amber", "Pausado"],
    bloqueado: ["badge--red", "Bloqueado"],
    concluido: ["badge--blue", "Concluído"],
  };
  const [cls, label] = map[status] || ["badge--gray", status || "—"];
  return `<span class="badge ${cls}">${escapeHtml(label)}</span>`;
}

function typeBadge(type) {
  const map = {
    receita: ["badge--green", "Receita"],
    despesa: ["badge--red", "Despesa"],
    transferencia: ["badge--blue", "Transferência"],
  };
  const [cls, label] = map[type] || ["badge--gray", type || "—"];
  return `<span class="badge ${cls}">${escapeHtml(label)}</span>`;
}

function moneyCell(amount, type) {
  const cls = type === "receita" || type === "transferencia" ? "amount-positive" : "amount-negative";
  return `<span class="${cls}">${formatBRL(amount)}</span>`;
}

function optionsHtml(records, selected, placeholder = "—") {
  let html = `<option value="">${placeholder}</option>`;
  for (const r of records || []) {
    const sel = r.id === selected ? " selected" : "";
    html += `<option value="${r.id}"${sel}>${escapeHtml(r.name || r.description || r.label || r.id)}</option>`;
  }
  return html;
}

function modalFormHtml({
  id, title, size = "", fieldsHtml, submitText = "Salvar", onSubmit,
}) {
  const overlay = document.createElement("div");
  overlay.className = `modal-overlay open`;
  overlay.innerHTML = `
    <div class="modal ${size}">
      <div class="modal__head"><h3>${escapeHtml(title)}</h3><button class="btn-icon" data-modal-close>✕</button></div>
      <form data-modal-form>
        <div class="modal__body"><div class="form-grid">${fieldsHtml}</div></div>
        <div class="modal__foot">
          <button type="button" class="btn btn--ghost" data-modal-close>Cancelar</button>
          <button type="submit" class="btn">${escapeHtml(submitText)}</button>
        </div>
      </form>
    </div>`;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });
  overlay.querySelectorAll("[data-modal-close]").forEach((b) =>
    b.addEventListener("click", () => overlay.remove())
  );
  overlay.querySelector("[data-modal-form]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());
    try {
      await onSubmit(payload);
      overlay.remove();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      btn.disabled = false;
    }
  });
  document.body.appendChild(overlay);
  return overlay;
}

function fieldHtml({ id, label, type = "text", value = "", required = false, options, placeholder, span2 = false }) {
  const cls = span2 ? ' field span2' : " field";
  const req = required ? " required" : "";
  let control = "";
  if (type === "select") {
    control = `<select id="${id}" name="${id}" class="input"${req}>${options || ""}</select>`;
  } else if (type === "textarea") {
    control = `<textarea id="${id}" name="${id}" class="input" rows="2">${escapeHtml(value)}</textarea>`;
  } else {
    control = `<input id="${id}" name="${id}" type="${type}" class="input" value="${escapeHtml(value)}" placeholder="${escapeHtml(placeholder || "")}"${req}>`;
  }
  return `<div class="${cls}"><label for="${id}">${escapeHtml(label)} ${required ? "<span style='color:var(--red)'>*</span>" : ""}</label>${control}</div>`;
}

function icon(name, size = 18) {
  if (window.feather && feather.icons[name]) {
    return feather.icons[name].toSvg({ width: size, height: size, "stroke-width": 2 });
  }
  return `<span style="font-size:${size - 6}px">[${name}]</span>`;
}

async function withData(fn) {
  const view = document.getElementById("view");
  view.innerHTML = loadingHtml();
  try {
    view.innerHTML = await fn();
  } catch (err) {
    view.innerHTML = `<div class="card"><div class="card__body" style="color:var(--red)">${escapeHtml(err.message)}</div></div>`;
  }
}