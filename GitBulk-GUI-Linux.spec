# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets', 'assets'), ('src/gui', 'gui'), ('src/gui/icons', 'src/gui/icons'), ('src/gui/theme.qss', 'src/gui/theme.qss')],
    hiddenimports=['PySide6.QtSvg', 'PySide6.QtSvgWidgets', 'PySide6.QtXml', 'PySide6.QtWidgets', 'PySide6.QtGui', 'gui.translations', 'gui.icon_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GitBulk-GUI-Linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
