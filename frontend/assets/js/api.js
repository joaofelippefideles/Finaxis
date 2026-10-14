/* ---------- Cliente HTTP (JWT) ---------- */

window.App = window.App || { views: {}, charts: {}, data: {} };

async function api(path, { method = "GET", body, query, form } = {}) {
  const headers = {};
  const token = localStorage.getItem("scfp_token");
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (form !== undefined) headers["Content-Type"] = "application/json";

  let url = "/api" + path;
  if (query) {
    const sp = new URLSearchParams();
    for (const k in query) {
      const v = query[k];
      if (v !== undefined && v !== null && v !== "") sp.set(k, v);
    }
    const qs = sp.toString();
    if (qs) url += "?" + qs;
  }

  let resp;
  try {
    resp = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : form !== undefined ? JSON.stringify(form) : undefined,
    });
  } catch (e) {
    throw new Error("Sem conexão com o servidor");
  }

  if (resp.status === 401) {
    logout();
    throw new Error("Sessão expirada");
  }

  const ct = resp.headers.get("content-type") || "";
  const data = ct.includes("json") ? await resp.json().catch(() => null) : await resp.text();

  if (!resp.ok) {
    let msg = "Erro na requisição";
    if (data && typeof data === "object") {
      if (Array.isArray(data.detail)) msg = data.detail.join("; ");
      else if (typeof data.detail === "string") msg = data.detail;
    } else if (typeof data === "string" && data) {
      msg = data;
    }
    throw new Error(msg);
  }
  return data;
}

async function apiDownload(path, { query } = {}) {
  const headers = {};
  const token = localStorage.getItem("scfp_token");
  if (token) headers.Authorization = `Bearer ${token}`;

  let url = "/api" + path;
  if (query) {
    const sp = new URLSearchParams();
    for (const k in query) {
      const v = query[k];
      if (v !== undefined && v !== null && v !== "") sp.set(k, v);
    }
    const qs = sp.toString();
    if (qs) url += "?" + qs;
  }

  let resp;
  try {
    resp = await fetch(url, { headers });
  } catch (e) {
    throw new Error("Sem conexão com o servidor");
  }

  if (resp.status === 401) {
    logout();
    throw new Error("Sessão expirada");
  }

  if (!resp.ok) {
    let msg = "Erro ao exportar relatório";
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("json")) {
      const data = await resp.json().catch(() => null);
      if (data) {
        if (Array.isArray(data.detail)) msg = data.detail.join("; ");
        else if (typeof data.detail === "string") msg = data.detail;
      }
    }
    throw new Error(msg);
  }

  const blob = await resp.blob();
  const filename =
    filenameFromDisposition(resp.headers.get("content-disposition")) || "relatorio";
  saveBlob(blob, filename);
  return filename;
}

function filenameFromDisposition(header) {
  if (!header) return null;
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (utf8) return decodeURIComponent(utf8[1]);
  const plain = /filename="?([^";]+)"?/i.exec(header);
  return plain ? plain[1].trim() : null;
}

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function authUser() {
  try {
    return JSON.parse(localStorage.getItem("scfp_user") || "null");
  } catch {
    return null;
  }
}

function logout() {
  localStorage.removeItem("scfp_token");
  localStorage.removeItem("scfp_user");
  location.href = "/login";
}