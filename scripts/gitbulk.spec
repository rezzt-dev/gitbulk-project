# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # GUI theme and icons bundled into the executable
        ('src/gui/theme.qss',   'gui'),
        ('src/gui/icons',       'gui/icons'),
        # App icon (also used at runtime for fallback)
        ('assets/gitbulk.ico',  'assets'),
    ],
    hiddenimports=[
        # Internal layers
        'persistence',
        'view',
        'model',
        # GUI
        'gui',
        'gui.app',
        'gui.main_window',
        'gui.workers',
        'gui.icon_manager',
        'PySide6',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        # GitPython
        'git',
        'git.exc',
        'git.repo',
        'git.repo.base',
        'git.objects',
        'git.refs',
        'git.index',
        'git.remote',
        # Rich UI
        'rich',
        'rich.console',
        'rich.panel',
        'rich.table',
        'rich.tree',
        'rich.prompt',
        'rich.progress',
        'rich.theme',
        'rich.markup',
        'rich.text',
        # Standard library
        'urllib.request',
        'urllib.error',
        'socket',
    ],
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
    name='gitbulk-windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # windowless: no CMD popup when launched as GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/gitbulk.ico',  # embeds icon into the .exe PE header
)
