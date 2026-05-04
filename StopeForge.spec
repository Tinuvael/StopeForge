# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


project_root = Path.cwd()
icon_path = project_root / "assets" / "icons" / "stopeforge_icon.ico"

datas = []

if (project_root / "assets").exists():
    datas.append(("assets", "assets"))


a = Analysis(
    ["run.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tests",
    ],
    noarchive=False,
)


pyz = PYZ(
    a.pure,
    a.zipped_data,
)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StopeForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon_path) if icon_path.exists() else None,
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="StopeForge",
)


if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="StopeForge.app",
        icon=str(icon_path) if icon_path.exists() else None,
        bundle_identifier="com.stopeforge.app",
    )
