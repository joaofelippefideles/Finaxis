# Guia de Uso — Finaxis (Sistema de Controle Financeiro Pessoal)

Guia rápido das funcionalidades do sistema, para o usuário final.

---

## 1. Acesso

1. Abra o programa pelo atalho do Menu Iniciar / Área de trabalho.
2. O navegador abre em `http://127.0.0.1:8000/login`.
3. **Primeiro uso:** clique em **Criar conta** (nome, e-mail e senha com 6+ caracteres).
4. Depois, entre com e-mail e senha.

As **categorias padrão** são criadas automaticamente no seu cadastro.

---

## 2. Recursos principais

| Área | Para que serve |
| --- | --- |
| **Dashboard** | Visão geral: saldo, receitas, despesas e gráficos do período. |
| **Lançamentos** | Registre receitas, despesas e transferências. |
| **Contas** | Cadastre contas (corrente, poupança, carteira, digital, investimentos). |
| **Categorias** | Organize lançamentos; crie/edite/ative-desative categorias. |
| **Cartões** | Cartões de crédito, faturas e parcelamentos. |
| **A pagar / A receber** | Controle de contas a pagar e a receber (pagar/reabrir). |
| **Orçamentos** | Defina limites por categoria e acompanhe o uso. |
| **Recorrentes** | Lançamentos que se repetem (diário, semanal, mensal, anual). |
| **Notificações** | Avisos de contas próximas/vencidas, orçamento, fatura, etc. |
| **Relatórios** | Resumo e **exportação** em CSV, Excel (XLSX) e PDF. |
| **Configurações** | Perfil, preferências e troca de senha. |

---

## 3. Fluxo sugerido

1. **Cadastre suas contas** (ex.: "Conta corrente", "Carteira").
2. **Revise as categorias** (já vêm categorias padrão).
3. **Registre lançamentos** vinculando conta e categoria.
4. **Defina orçamentos** por categoria para acompanhar limites.
5. **Use o Dashboard** para acompanhar o mês.
6. **Exporte relatórios** quando precisar compartilhar/arquivar.

---

## 4. Relatórios e exportação

Em **Relatórios**, escolha o período e os filtros e exporte:

- **CSV** — abre no Excel/planilhas.
- **XLSX** — planilha Excel formatada.
- **PDF** — documento pronto para impressão.

O download é autenticado (feito pelo próprio sistema, com o seu login).

---

## 5. Onde ficam os meus dados

- Todos os dados são gravados em **arquivos JSON** na pasta `data` da instalação
  (por padrão `%LOCALAPPDATA%\Programs\SistemaFinanceiro\data`).
- **Nada é enviado para a internet.** O sistema é totalmente local.
- Os dados **sobrevivem** a atualizações e à desinstalação do programa.

### Backup manual

- Copie a pasta `data` para um local seguro, **ou**
- Use o script de backup do projeto (ver `docs/GUIA-DE-EXECUCAO.md`).

Os backups ficam em `backups\backup-AAAA-MM-DD-HHMMSS\`.

---

## 6. Dicas

- Para **fechar** o sistema, use o botão **Encerrar** na janela de controle.
- Se abrir o atalho novamente, o sistema apenas reabre o navegador (não duplica).
- Valores monetários usam duas casas decimais; datas no formato `AAAA-MM-DD`.