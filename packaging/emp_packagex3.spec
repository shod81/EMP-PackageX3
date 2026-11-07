# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for EMP-PackageX3 (Onedir). Build: uv run pyinstaller packaging/emp_packagex3.spec

from pathlib import Path

_SPEC_DIR = Path(SPECPATH).resolve()
_ICON = str((_SPEC_DIR / ".." / "src" / "emp_packagex3" / "resources" / "emp_packagex3.ico").resolve())
_PNG = str((_SPEC_DIR / ".." / "src" / "emp_packagex3" / "resources" / "emp_packagex3.png").resolve())
_VERSION_JSON = str((_SPEC_DIR / ".." / "packaging" / "VERSION.json").resolve())

a = Analysis(
    ['../src/emp_packagex3/__main__.py'],
    pathex=['../src'],
    binaries=[],
    datas=[
        (_ICON, 'emp_packagex3/resources'),
        (_PNG, 'emp_packagex3/resources'),
        (_VERSION_JSON, 'packaging'),
    ],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EMP-PackageX3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ICON,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EMP-PackageX3',
)
