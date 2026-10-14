/* ---------- App shell / router ---------- */

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("scfp_token");
  if (!token) {
    location.href = "/login";
    return;
  }
  App.navigate = navigate;

  hydrateUser();
  bindSearch();
  bindNotifications();
  bindSidebar();
  loadNotifications();

  window.addEventListener("hashchange", () => {
    closeSidebar();
    navigate();
  });
  navigate();
});

function currentRoute() {
  const hash = location.hash.replace(/^#\/?/, "");
  return hash.split("?")[0].split("/")[0] || "dashboard";
}

async function navigate(route) {
  route = route || currentRoute();
  const view = App.views[route] || App.views.dashboard;
  location.hash = route === "dashboard" ? "#/dashboard" : `#/${route}`;

  document.querySelectorAll(".sidebar__link").forEach((l) =>
    l.classList.toggle("active", l.dataset.route === route)
  );

  const pageHead = document.getElementById("page-title");
  if (pageHead) {
    pageHead.textContent = view.title;
    document.getElementById("page-subtitle").textContent = view.subtitle;
  }

  try {
    const html = await view.render();
    const viewEl = document.getElementById("view");
    viewEl.innerHTML = html;
    if (view.init) await view.init();
  } catch (err) {
    const viewEl = document.getElementById("view");
    viewEl.innerHTML = `<div class="card"><div class="card__body" style="color:var(--red)">${escapeHtml(err.message)}</div></div>`;
  }
}

function hydrateUser() {
  const user = authUser();
  if (!user) return;
  const avatar = document.getElementById("user-avatar");
  const nameEl = document.getElementById("user-name");
  const mailEl = document.getElementById("user-mail");
  if (avatar) avatar.textContent = (user.name || "U").charAt(0).toUpperCase();
  if (nameEl) nameEl.textContent = user.name || "Usuário";
  if (mailEl) mailEl.textContent = user.email || "";
}

function bindSearch() {
  const input = document.getElementById("top-search");
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && input.value.trim()) {
      navigate(`search?q=${encodeURIComponent(input.value.trim())}`);
    }
  });
}

function bindSidebar() {
  document.querySelectorAll(".sidebar__link").forEach((l) => {
    l.addEventListener("click", (e) => {
      e.preventDefault();
      navigate(l.dataset.route);
    });
  });
  document.querySelectorAll(".menu-toggle").forEach((b) => {
    b.addEventListener("click", () => document.querySelector(".sidebar")?.classList.toggle("open"));
  });
  document.getElementById("btn-logout")?.addEventListener("click", (e) => {
    e.preventDefault();
    logout();
  });
}

function closeSidebar() {
  document.querySelector(".sidebar")?.classList.remove("open");
}

/* ---------- Notificações ---------- */

async function loadNotifications() {
  try {
    const count = await api("/notifications/unread-count");
    const badge = document.getElementById("notif-count");
    if (badge) {
      if (count.unread > 0) {
        badge.textContent = count.unread > 9 ? "9+" : count.unread;
        badge.style.display = "flex";
      } else {
        badge.style.display = "none";
      }
    }
  } catch { /* offline */ }
}

function bindNotifications() {
  const btn = document.getElementById("notif-toggle");
  const panel = document.getElementById("notif-panel");
  if (!btn || !panel) return;

  btn.addEventListener("click", async () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      renderNotifications();
    }
  });
  document.addEventListener("click", (e) => {
    if (!btn.contains(e.target) && !panel.contains(e.target)) {
      panel.classList.remove("open");
    }
  });
}

async function renderNotifications() {
  const panel = document.getElementById("notif-panel");
  try {
    const items = await api("/notifications");
    if (!items.length) {
      panel.innerHTML = `<div class="empty-state" style="padding:30px 16px">Sem notificações</div>`;
      return;
    }
    panel.innerHTML = `
      <div style="display:flex;justify-content:flex-end;padding:4px 6px 6px">
        <button class="btn btn--sm btn--ghost" id="notif-marks">Marcar todas como lidas</button>
      </div>
      ${items.map((n) => `
        <div class="notif-item ${n.is_read ? "" : "unread"}" data-id="${n.id}">
          <div class="notif-item__title">${escapeHtml(n.title)}</div>
          <div class="notif-item__msg">${escapeHtml(n.message)}</div>
          <div class="notif-item__time">${new Date(n.created_at).toLocaleString("pt-BR")}</div>
        </div>`).join("")}`;
    panel.querySelectorAll(".notif-item").forEach((item) => {
      item.addEventListener("click", async () => {
        if (!item.classList.contains("unread")) return;
        try {
          await api(`/notifications/${item.dataset.id}/read`, { method: "POST" });
          item.classList.remove("unread");
          loadNotifications();
        } catch { /* noop */ }
      });
    });
    panel.querySelector("#notif-marks")?.addEventListener("click", async () => {
      try {
        await api("/notifications/read-all", { method: "POST" });
        renderNotifications();
        loadNotifications();
      } catch (err) { toast(err.message, "error"); }
    });
  } catch (err) {
    panel.innerHTML = `<div class="empty-state" style="padding:30px 16px">${escapeHtml(err.message)}</div>`;
  }
}