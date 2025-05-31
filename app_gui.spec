# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['G:\\My Drive\\python\\CleanIncomings\\app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('G:\\My Drive\\python\\CleanIncomings\\icons', 'icons/'), ('G:\\My Drive\\python\\CleanIncomings\\config', 'config/'), ('G:\\My Drive\\python\\CleanIncomings\\docs', 'docs/'), ('G:\\My Drive\\python\\CleanIncomings\\python', 'python/'), ('G:\\My Drive\\python\\CleanIncomings\\scripts', 'scripts/'), ('G:\\My Drive\\python\\CleanIncomings\\themes', 'themes/')],
    hiddenimports=['customtkinter', 'PIL'],
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
    name='app_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='app_gui',
)
