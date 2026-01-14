# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['latc_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['sklearn.utils._typedefs', 'sklearn.utils._heap', 'sklearn.utils._sorting', 'sklearn.utils._vector_sentinel', 'tkinter', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'PIL', 'serie_horaria_completa', 'comparacao_contadores', 'gap_analysis', 'latc_advanced', 'latc_simple', 'progress_tracker'],
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
    name='LATC_Tool_GUI',
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
    icon='icon.ico',
)
