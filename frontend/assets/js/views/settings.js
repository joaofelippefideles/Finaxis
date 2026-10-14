/* ---------- Configurações ---------- */

App.views.settings = {
  route: "settings",
  title: "Configurações",
  subtitle: "Perfil, preferências e segurança",
  async render() {
    const s = await api("/settings");
    App.data.accountList = s.accounts;
    App.data.cardList = s.cards;
    const accRows = (s.accounts || []).map((a) =>
      `<tr><td class="td-strong">${escapeHtml(a.name)}</td><td>${escapeHtml(a.bank || "—")}</td><td class="text-right">${formatBRL(a.balance)}</td></tr>`).join("");
    const cardRows = (s.cards || []).map((c) =>
      `<tr><td class="td-strong">${escapeHtml(c.name)}</td><td>${escapeHtml(c.bank || "—")}</td><td class="text-right">${formatBRL(c.limit_amount)}</td></tr>`).join("");

    return `
      <div class="grid two">
        <div class="card">
          <div class="card__head"><h3>Perfil</h3></div>
          <div class="card__body">
            <form id="profile-form" class="form-grid">
              ${fieldHtml({ id: "name", label: "Nome", value: s.profile.name, required: true })}
              ${fieldHtml({ id: "email", label: "E-mail", type: "email", value: s.profile.email, required: true })}
              <div class="span2"><button class="btn" type="submit">Salvar perfil</button></div>
            </form>
          </div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Preferências</h3></div>
          <div class="card__body">
            <form id="prefs-form" class="form-grid">
              <div class="field"><label for="currency">Moeda</label>
                <select id="currency" name="currency" class="input">
                  <option value="BRL" ${s.profile.currency === "BRL" ? "selected" : ""}>BRL - Real</option>
                  <option value="USD" ${s.profile.currency === "USD" ? "selected" : ""}>USD - Dólar</option>
                  <option value="EUR" ${s.profile.currency === "EUR" ? "selected" : ""}>EUR - Euro</option>
                </select>
              </div>
              <div class="field"><label for="date_format">Formato de data</label>
                <select id="date_format" name="date_format" class="input">
                  <option value="DD/MM/YYYY" ${s.profile.date_format === "DD/MM/YYYY" ? "selected" : ""}>DD/MM/YYYY</option>
                  <option value="YYYY-MM-DD" ${s.profile.date_format === "YYYY-MM-DD" ? "selected" : ""}>YYYY-MM-DD</option>
                </select>
              </div>
              <div class="field"><label for="locale">Localidade</label>
                <select id="locale" name="locale" class="input">
                  <option value="pt_BR" ${s.profile.locale === "pt_BR" ? "selected" : ""}>pt_BR</option>
                  <option value="en_US" ${s.profile.locale === "en_US" ? "selected" : ""}>en_US</option>
                </select>
              </div>
              <div class="span2"><button class="btn" type="submit">Salvar preferências</button></div>
            </form>
          </div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Alterar senha</h3></div>
          <div class="card__body">
            <form id="password-form" class="form-grid">
              ${fieldHtml({ id: "current_password", label: "Senha atual", type: "password", required: true, span2: true })}
              ${fieldHtml({ id: "new_password", label: "Nova senha", type: "password", required: true, span2: true })}
              <div class="span2"><button class="btn" type="submit">Alterar senha</button></div>
            </form>
          </div>
        </div>
        <div class="card">
          <div class="card__head"><h3>Resumo</h3></div>
          <div class="card__body">
            <div class="td-strong mb-8">Contas (${(s.accounts || []).length})</div>
            <div class="table-wrap"><table class="data">
              <thead><tr><th>Nome</th><th>Banco</th><th class="text-right">Saldo</th></tr></thead>
              <tbody>${accRows || `<tr><td colspan="3">${emptyHtml("Sem contas")}</td></tr>`}</tbody>
            </table></div>
            <div class="td-strong mt-8 mb-8">Cartões (${(s.cards || []).length})</div>
            <div class="table-wrap"><table class="data">
              <thead><tr><th>Nome</th><th>Banco</th><th class="text-right">Limite</th></tr></thead>
              <tbody>${cardRows || `<tr><td colspan="3">${emptyHtml("Sem cartões")}</td></tr>`}</tbody>
            </table></div>
          </div>
        </div>
      </div>`;
  },
  init() {
    document.getElementById("profile-form")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      try {
        const user = await api("/settings/profile", { method: "PUT", body: payload });
        localStorage.setItem("scfp_user", JSON.stringify(user));
        toast("Perfil atualizado", "success");
        App.navigate("settings");
      } catch (err) { toast(err.message, "error"); }
    });
    document.getElementById("prefs-form")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      try {
        await api("/settings/preferences", { method: "PUT", body: payload });
        toast("Preferências salvas", "success");
      } catch (err) { toast(err.message, "error"); }
    });
    document.getElementById("password-form")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      const btn = e.target.querySelector("button");
      btn.disabled = true;
      try {
        await api("/settings/password", { method: "PUT", body: payload });
        toast("Senha alterada com sucesso", "success");
        e.target.reset();
      } catch (err) {
        toast(err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
  },
};