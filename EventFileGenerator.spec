# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Event File Generator (Windows .exe and macOS app).
# CustomTkinter requires --onedir and bundled data files; use this spec with:
#   pyinstaller EventFileGenerator.spec

import os
import sys

# Bundle CustomTkinter data files (themes, assets) - required for CTk to run
try:
    import customtkinter as _ctk
    _ctk_dir = os.path.dirname(_ctk.__file__)
    _datas = [(_ctk_dir, 'customtkinter')]
except Exception:
    _datas = []

_spec_dir = os.path.dirname(os.path.abspath(SPEC))
_layout_dir = os.path.join(_spec_dir, 'assets', 'layout_previews')
if os.path.isdir(_layout_dir):
    _datas.append((_layout_dir, os.path.join('assets', 'layout_previews')))

a = Analysis(
    ['event_folder_generator.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=['customtkinter', 'PIL', 'PIL.Image', 'PIL.ImageDraw'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# One-file executable (extracts to temp at runtime).
# CustomTkinter docs suggest onedir for data files; onefile often works when datas are set.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EventFileGenerator',
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
    icon=None,
)

# On macOS, wrap the one-file binary in a double-clickable .app
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
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
