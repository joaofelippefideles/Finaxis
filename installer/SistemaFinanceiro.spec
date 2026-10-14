# -*- mode: python ; coding: utf-8 -*-
"""Receita PyInstaller (onedir) do Finaxis (Sistema de Controle Financeiro Pessoal).

Gera uma pasta autocontida `SistemaFinanceiro/` com:
    SistemaFinanceiro.exe   -> inicializador desktop (installer/launcher.py)
    _internal/              -> runtime Python + dependências
O frontend, a pasta ``data`` e a pasta ``backups`` são instalados AO LADO
do executável (não entram aqui), garantindo a independência dos dados.

Uso: pyinstaller installer/SistemaFinanceiro.spec
"""

from pathlib import Path
import os

from PyInstaller.utils.hooks import collect_submodules

_console = os.environ.get("SCF_CONSOLE") == "1"

spec_dir = Path(SPECPATH).resolve()
project_root = spec_dir.parent
backend_dir = project_root / "backend"

hidden_imports = (
    collect_submodules("app")
    + collect_submodules("openpyxl")
    + [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "email_validator",
    ]
)

a = Analysis(
    [str(Path(SPECPATH) / "launcher.py")],
    pathex=[str(Path(SPECPATH).parent / "backend")],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SistemaFinanceiro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=_console,
    disable_windowed_traceback=False,
    icon=(str(Path(SPECPATH) / "app.ico")
          if (Path(SPECPATH) / "app.ico").exists() else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SistemaFinanceiro",
)