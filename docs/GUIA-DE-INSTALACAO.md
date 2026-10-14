# Guia de Instalação — Windows

Este guia descreve como **instalar o Finaxis (Sistema de Controle Financeiro
Pessoal)** a partir do instalador (`FinaxisSetup.exe`) e como gerar esse
instalador a partir do código-fonte.

---

## 1. Instalação a partir do instalador

### O que você precisa

- Windows 10/11 (64 bits).
- Nenhuma instalação de banco de dados.
- Nenhum Python necessário (o executável é autocontido).

### Passo a passo

1. Baixe/copíe o arquivo `FinaxisSetup.exe`.
2. Clique duas vezes e siga o assistente (**Avançar → Instalar**).
3. Ao final, marque **Executar o Sistema** (ou abra pelo Menu Iniciar).
4. O sistema abre no navegador padrão em `http://127.0.0.1:8000/login`.

### Onde os arquivos são gravados

| Item | Local |
| --- | --- |
| Programa (executável) | `%LOCALAPPDATA%\Programs\SistemaFinanceiro` |
| Seus dados (JSON) | `%LOCALAPPDATA%\Programs\SistemaFinanceiro\data` |
| Backups | `%LOCALAPPDATA%\Programs\SistemaFinanceiro\backups` |
| Logs | `%LOCALAPPDATA%\Programs\SistemaFinanceiro\logs` |

A instalação é **por usuário**, portanto **não exige administrador**.

### Atalhos criados

- **Menu Iniciar → Finaxis**
- **Desinstalar** (no mesmo grupo do Menu Iniciar)
- **Área de trabalho** (opcional, marcado durante a instalação)

---

## 2. Usando o programa

Ao abrir, o programa:

1. garante as pastas `data` e `backups`;
2. inicia o servidor local em `127.0.0.1:8000`;
3. abre o navegador automaticamente;
4. exibe uma pequena janela com os botões **Abrir no navegador** e **Encerrar**.

Para **fechar o sistema**, clique em **Encerrar** na janela de controle (ou feche
essa janela). Evitar encerrar pelo Gerenciador de Tarefas.

> Abrir o atalho com o sistema já em execução **não** cria uma segunda instância:
> apenas traz o navegador de volta.

---

## 3. Atualização (nova versão)

1. Execute o novo `FinaxisSetup.exe` no **mesmo computador/usuário**.
2. O instalador atualiza os arquivos do programa **sem apagar** as pastas
   `data` e `backups`. Seus lançamentos e configurações são preservados.
3. Não é necessário desinstalar antes.

---

## 4. Desinstalação

Use **Configurações → Aplicativos** (ou **Menu Iniciar → Desinstalar**).

- Os arquivos do programa são removidos.
- **Seus dados (`data` e `backups`) são preservados** por segurança.

> Para apagar também os dados, remova manualmente a pasta
> `%LOCALAPPDATA%\Programs\SistemaFinanceiro` após desinstalar.

---

## 5. Gerar o instalador a partir do código-fonte

### Pré-requisitos

- **Python 3.12+** (testado com 3.14) e **Node.js** (para testes do frontend).
- **[Inno Setup 6](https://jrsoftware.org/isdl.php)** — necessário para compilar o
  `FinaxisSetup.exe`. Instale com:

  ```powershell
  winget install --id JRSoftware.InnoSetup -e
  ```

### Passos

```powershell
# 1. Gera o executável (PyInstaller) e o instalador (Inno Setup)
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

O script:

1. cria um ambiente de build limpo em `backend\.venv-build`;
2. instala as dependências + PyInstaller;
3. gera o executável em `installer\output\pyinstaller\SistemaFinanceiro`;
4. monta o **payload** em `installer\payload\SistemaFinanceiro` (executável + frontend + docs);
5. compila `installer\SistemaFinanceiro.iss` com o Inno Setup.

Resultado final:

```
dist\FinaxisSetup.exe
```

### Somente o executável (sem Inno Setup)

```powershell
powershell -ExecutionPolicy Bypass -File installer\build.ps1 -SkipInstaller
```

O executável autocontido fica em `installer\payload\SistemaFinanceiro`.

### Testar o pacote gerado

```powershell
powershell -ExecutionPolicy Bypass -File installer\test_package.ps1
```

O teste inicia o executável, valida autenticação, CRUD, relatórios/exportações,
instância única e persistência após reinício.

---

## 6. Solução de problemas

| Sintoma | Causa provável / solução |
| --- | --- |
| Nada abre no navegador | Verifique a janela de controle; abra `http://127.0.0.1:8000` manualmente. |
| "porta 8000 já em uso" | Outro programa usa a porta. Feche-o e abra o sistema novamente. |
| Falha ao iniciar | Veja o arquivo `data\startup-error.log` e `logs\app.log`. |
| Antivírus bloqueia | Permita o programa (o executável não é assinado digitalmente). |