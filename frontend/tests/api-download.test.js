/* Testes do fluxo de download autenticado (apiDownload em api.js). */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const API_SOURCE = fs.readFileSync(
  path.join(__dirname, "..", "assets", "js", "api.js"),
  "utf8",
);

function fakeResponse({
  status = 200,
  contentType = "application/pdf",
  disposition = 'attachment; filename="relatorio-2026-01-01-2026-12-31.pdf"',
  json = null,
} = {}) {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: {
      get(name) {
        const key = String(name).toLowerCase();
        if (key === "content-type") return contentType;
        if (key === "content-disposition") return disposition;
        return null;
      },
    },
    async blob() {
      return { type: contentType, body: "conteudo" };
    },
    async json() {
      return json;
    },
    async text() {
      return "conteudo";
    },
  };
}

function makeSandbox({ token = "tok-123", response = fakeResponse() } = {}) {
  const calls = { fetch: [], created: [], clicked: [], revoked: [] };
  const removals = [];

  const document = {
    createElement() {
      const el = { href: "", download: "", click: () => calls.clicked.push(el), remove: () => {} };
      return el;
    },
    body: { appendChild: () => {} },
  };

  const sandbox = {
    console,
    localStorage: {
      getItem: (k) => (k === "scfp_token" ? token : null),
      removeItem: (k) => removals.push(k),
    },
    location: { href: "" },
    document,
    URL: {
      createObjectURL: (blob) => {
        calls.created.push(blob);
        return "blob:fake-url";
      },
      revokeObjectURL: (u) => calls.revoked.push(u),
    },
    URLSearchParams,
    setTimeout: (fn) => fn(),
    fetch: async (url, opts) => {
      calls.fetch.push({ url, opts });
      return response;
    },
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(API_SOURCE, sandbox);
  return { sandbox, calls, removals, document };
}

test("envia Authorization Bearer e monta a query do endpoint correto", async () => {
  const { sandbox, calls } = makeSandbox({ token: "meu-token" });
  await sandbox.apiDownload("/reports/export", {
    query: {
      fmt: "pdf",
      start_date: "2026-01-01",
      end_date: "2026-12-31",
      category_id: "",
      account_id: "acc-1",
    },
  });

  assert.equal(calls.fetch.length, 1);
  assert.equal(
    calls.fetch[0].url,
    "/api/reports/export?fmt=pdf&start_date=2026-01-01&end_date=2026-12-31&account_id=acc-1",
  );
  assert.equal(calls.fetch[0].opts.headers.Authorization, "Bearer meu-token");
});

test("dispara o download usando o filename do Content-Disposition", async () => {
  const { sandbox, calls } = makeSandbox({
    response: fakeResponse({
      disposition: 'attachment; filename="relatorio-2026-01-01-2026-12-31.xlsx"',
    }),
  });
  const filename = await sandbox.apiDownload("/reports/export", {
    query: { fmt: "xlsx", start_date: "2026-01-01", end_date: "2026-12-31" },
  });

  assert.equal(filename, "relatorio-2026-01-01-2026-12-31.xlsx");
  assert.equal(calls.created.length, 1);
  assert.equal(calls.clicked.length, 1);
  assert.equal(calls.clicked[0].download, "relatorio-2026-01-01-2026-12-31.xlsx");
  assert.deepEqual(calls.revoked, ["blob:fake-url"]);
});

test("sem token, nao envia header Authorization", async () => {
  const { sandbox, calls } = makeSandbox({ token: null });
  await sandbox.apiDownload("/reports/export", {
    query: { fmt: "csv", start_date: "2026-01-01", end_date: "2026-12-31" },
  });
  assert.equal(calls.fetch[0].opts.headers.Authorization, undefined);
  assert.equal(
    calls.fetch[0].url,
    "/api/reports/export?fmt=csv&start_date=2026-01-01&end_date=2026-12-31",
  );
});

test("401 encerra a sessao (logout) e lanca erro", async () => {
  const { sandbox, removals } = makeSandbox({
    response: fakeResponse({ status: 401, contentType: "application/json" }),
  });

  await assert.rejects(
    () => sandbox.apiDownload("/reports/export", { query: { fmt: "pdf" } }),
    /Sessão expirada/,
  );
  assert.equal(sandbox.location.href, "/login");
  assert.deepEqual(removals, ["scfp_token", "scfp_user"]);
});

test("resposta de erro JSON propaga a mensagem de detail", async () => {
  const { sandbox, calls } = makeSandbox({
    response: fakeResponse({
      status: 400,
      contentType: "application/json",
      json: { detail: "Período inválido" },
    }),
  });

  await assert.rejects(
    () => sandbox.apiDownload("/reports/export", { query: { fmt: "pdf" } }),
    /Período inválido/,
  );
  assert.equal(calls.clicked.length, 0);
});