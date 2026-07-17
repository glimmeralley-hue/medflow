# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_refactored.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('medflow-icon.svg', './'),
        ('requirements.txt', './'),
    ],
    hiddenimports=[
        'PySide6.QtCharts',
        'PySide6.QtMultimedia',
        'medflow.ui',
        'medflow.database',
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
    name='MedFlow',
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
