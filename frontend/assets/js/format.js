/* ---------- Formatação (BRL / datas pt-BR) ---------- */

function formatBRL(value) {
  const n = Number(value);
  if (!isFinite(n)) return "R$ 0,00";
  return n.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function parseBrl(str) {
  if (typeof str === "number") return str;
  if (str === null || str === undefined) return NaN;
  let v = String(str).replace(/[R$\s]/g, "");
  if (v === "") return NaN;
  if (v.includes(",")) {
    v = v.replace(/\./g, "").replace(",", ".");
  }
  const n = parseFloat(v);
  return isNaN(n) ? NaN : n;
}

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + (iso.length <= 10 ? "T00:00:00" : ""));
  if (isNaN(d.getTime())) return String(iso);
  return d.toLocaleDateString("pt-BR");
}

function todayISO() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthsBack(n) {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function lastDayOfMonth(ym) {
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m, 0).getDate();
}

function monthLabel(ym) {
  const [y, m] = ym.split("-").map(Number);
  const names = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  return `${names[m - 1]}/${String(y).slice(2)}`;
}

function ucfirst(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}