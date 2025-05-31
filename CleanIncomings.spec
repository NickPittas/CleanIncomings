# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_gui.py'],
    pathex=['./python'],
    binaries=[],
    datas=[('config', 'config'), ('themes', 'themes'), ('icons', 'icons'), ('python/_progress', 'python/_progress'), ('user_settings.json', '.'), ('python/requirements.txt', 'python')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'customtkinter', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'queue', 'Pillow'],
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
    name='CleanIncomings',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CleanIncomings',
)
