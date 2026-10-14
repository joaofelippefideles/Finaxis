"""Inicializador desktop do Finaxis (Sistema de Controle Financeiro Pessoal).

Este é o ponto de entrada do executável empacotado (PyInstaller). Ele:

1. garante que as pastas ``data`` e ``backups`` existam ao lado do executável;
2. aponta a aplicação para o frontend externo;
3. cria/recupera uma chave de assinatura JWT local (nunca embutida no pacote);
4. inicia o servidor Uvicorn em 127.0.0.1:8000 (processo único);
5. abre o navegador padrão;
6. exibe uma janela com botão para encerrar o servidor.

Os dados do usuário ficam SEMPRE fora do executável (pastas ``data`` e
``backups``), portanto sobrevivem a atualizações e desinstalações.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}/"
APP_TITLE = "Finaxis"


def base_dir() -> Path:
    """Diretório base: pasta do executável (empacotado) ou raiz do projeto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def prepare_environment(base: Path) -> None:
    # Aplicativos sem console (PyInstaller windowed) têm sys.stdout/stderr = None,
    # o que quebra logging.StreamHandler do Uvicorn. Aponta para um destino nulo
    # (os logs reais continuam em data\logs\app.log).
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    data_dir = base / "data"
    backup_dir = base / "backups"
    frontend_dir = base / "frontend"
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["BACKUP_DIR"] = str(backup_dir)
    os.environ.setdefault("LOG_DIR", str(base / "logs"))
    if frontend_dir.exists():
        os.environ["FRONTEND_DIR"] = str(frontend_dir)

    # Chave JWT local e persistente (gerada no primeiro uso, não vai no pacote).
    if not os.environ.get("SECRET_KEY"):
        key_file = data_dir / ".secret_key"
        if key_file.exists():
            os.environ["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()
        else:
            import secrets

            key = secrets.token_hex(32)
            key_file.write_text(key, encoding="utf-8")
            os.environ["SECRET_KEY"] = key


def open_browser_if_enabled() -> None:
    """Abre o navegador padrão, exceto em testes (SCF_NO_BROWSER=1)."""
    if os.environ.get("SCF_NO_BROWSER") == "1":
        return
    webbrowser.open(APP_URL)


def server_responding() -> bool:
    try:
        with urllib.request.urlopen(f"{APP_URL}health", timeout=1.0) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return resp.status == 200 and "Finaxis" in body
    except Exception:
        return False


def port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((HOST, PORT)) == 0


def start_server():
    from app.main import app as fastapi_app

    import uvicorn

    config = uvicorn.Config(
        fastapi_app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server, thread


def wait_until_ready(timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if server_responding():
            return True
        time.sleep(0.2)
    return False


def run_control_window(server, thread) -> None:
    """Janela simples para encerrar o servidor com segurança."""
    try:
        import tkinter as tk

        root = tk.Tk()
    except Exception:
        # Sem interface gráfica: mantém o processo vivo enquanto o servidor roda.
        try:
            thread.join()
        except KeyboardInterrupt:
            server.should_exit = True
        return

    root.title(APP_TITLE)
    root.geometry("460x210")
    root.resizable(False, False)

    frame = tk.Frame(root, padx=20, pady=16)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text=APP_TITLE, font=("Segoe UI", 12, "bold")).pack(anchor="w")
    tk.Label(
        frame,
        text=f"Servidor ativo em {APP_URL}",
        font=("Segoe UI", 9),
        fg="#2e7d32",
    ).pack(anchor="w", pady=(6, 2))
    tk.Label(
        frame,
        text="Feche esta janela para encerrar o sistema.",
        font=("Segoe UI", 9),
        fg="#555555",
    ).pack(anchor="w", pady=(0, 12))

    def open_browser() -> None:
        webbrowser.open(APP_URL)

    def shutdown() -> None:
        server.should_exit = True
        root.after(150, root.destroy)

    buttons = tk.Frame(frame)
    buttons.pack(anchor="w")
    tk.Button(buttons, text="Abrir no navegador", command=open_browser, width=20).pack(
        side="left", padx=(0, 8)
    )
    tk.Button(buttons, text="Encerrar", command=shutdown, width=12).pack(side="left")

    root.protocol("WM_DELETE_WINDOW", shutdown)
    root.mainloop()

    server.should_exit = True
    thread.join(timeout=10)


def main() -> int:
    base = base_dir()
    prepare_environment(base)

    # Processo único: se o nosso servidor já está no ar, apenas abre o navegador.
    if server_responding():
        open_browser_if_enabled()
        return 0
    if port_in_use():
        # Porta ocupada por outro processo: informa e abre o navegador mesmo assim.
        print(f"Aviso: a porta {PORT} já está em uso por outro programa.")
        return 1

    server, thread = start_server()

    if not wait_until_ready():
        server.should_exit = True
        thread.join(timeout=5)
        _show_error(
            "Não foi possível iniciar o servidor. "
            f"Verifique se a porta {PORT} está livre e tente novamente."
        )
        return 2

    open_browser_if_enabled()
    run_control_window(server, thread)
    return 0


def _show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror(APP_TITLE, message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def _write_startup_error(exc: BaseException) -> None:
    """Registra falhas de inicialização em data\startup-error.log."""
    try:
        import traceback

        base = base_dir()
        base.mkdir(parents=True, exist_ok=True)
        with open(base / "startup-error.log", "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=fh)
            fh.write("\n")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        _write_startup_error(exc)
        _show_error(
            "Falha ao iniciar o Finaxis.\n"
            "Detalhes em: data\\startup-error.log"
        )
        raise