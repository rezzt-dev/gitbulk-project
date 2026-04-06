# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\repositorios\\desktop-projects\\gitbulk-project\\scripts\\..\\src\\main.py'],
    pathex=['D:\\repositorios\\desktop-projects\\gitbulk-project\\scripts\\..\\src'],
    binaries=[],
    datas=[('D:\\repositorios\\desktop-projects\\gitbulk-project\\scripts\\..\\assets', 'assets'), ('D:\\repositorios\\desktop-projects\\gitbulk-project\\scripts\\..\\src\\gui\\icons', 'gui/icons'), ('D:\\repositorios\\desktop-projects\\gitbulk-project\\scripts\\..\\src\\gui\\theme.qss', 'gui')],
    hiddenimports=['PySide6.QtSvg', 'PySide6.QtSvgWidgets'],
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
    [],
    exclude_binaries=True,
    name='GitBulk',
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
    icon=['D:\\repositorios\\desktop-projects\\gitbulk-project\\assets\\gitbulk.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GitBulk',
)
