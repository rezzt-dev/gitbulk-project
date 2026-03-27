# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Internal layers
        'persistence',
        'view',
        'model',
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
        # Standard library (occasionally missed by PyInstaller)
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
