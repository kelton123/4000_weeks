# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../4000_weeks.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../icons', 'icons'),
        ],
    hiddenimports=[],
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
    a.binaries,        # Required for --onefile mode
    a.zipfiles,        # Required for --onefile mode
    a.datas,           # Required for --onefile mode
    [],
    name='4000 Weeks',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,     # Equivalent to --windowed (hides terminal window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../icons/app_icon_transparent.ico',  # Sets your custom application icon
)