# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件，用于将 ComicForge FastAPI 后端打包为独立可执行文件。
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

project_root = Path.cwd()
source_path = project_root / "src"
import sys
if str(source_path) not in sys.path:
    sys.path.insert(0, str(source_path))

# 收集第三方库资源
packages_to_collect = [
    "fastapi",
    "httpx",
    "jinja2",
    "loguru",
    "langchain",
    "langchain_community",
    "langchain_openai",
    "langchain_ollama",
    "langgraph",
    "pydantic",
    "sqlmodel",
    "uvicorn",
]

config_path = project_root / "config.json"
alternate_config_path = project_root / "storage" / "config.json"

resolved_config_path = None
if config_path.exists():
    resolved_config_path = config_path
elif alternate_config_path.exists():
    resolved_config_path = alternate_config_path

datas = []

if resolved_config_path:
    datas.append((str(resolved_config_path), "config.json"))

datas.extend(
    [
        (str(project_root / "storage"), "storage"),
        (str(source_path / "api"), "api"),
    ]
)
binaries = []
hiddenimports = [
    "loguru",
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.websocket",
    "uvicorn.protocols.websockets.auto",
]

for package in packages_to_collect:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

block_cipher = None


a = Analysis(
    ["src/api/__main__.py"],
    pathex=[str(source_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ComicForgeBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ComicForgeBackend",
)


