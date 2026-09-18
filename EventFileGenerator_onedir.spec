# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Event File Generator — ONEDIR (folder output).
# Use this if the onefile build fails at runtime (e.g. CustomTkinter data not found).
# Build: pyinstaller EventFileGenerator_onedir.spec
# Output: dist/EventFileGenerator/EventFileGenerator.exe (Windows) or EventFileGenerator (macOS)

import os
import sys

try:
    import customtkinter as _ctk
    _ctk_dir = os.path.dirname(_ctk.__file__)
    _datas = [(_ctk_dir, 'customtkinter')]
except Exception:
    _datas = []

a = Analysis(
    ['event_folder_generator.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=['customtkinter', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'updater'],
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
    name='EventFileGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='EventFileGenerator',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='EventFileGenerator.app',
        icon=None,
        bundle_identifier='com.photoboothto.eventfilegenerator',
        info_plist={
            'CFBundleName': 'Event File Generator',
            'CFBundleDisplayName': 'Event File Generator',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
