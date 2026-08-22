# Building Event File Generator as EXE

This guide explains how to create a standalone Windows executable (.exe) from the Python script.

## Prerequisites

- Python 3.7+ on Windows, added to PATH
- Dependencies (CustomTkinter, etc.) are installed automatically by the build script

## Quick Build

1. **Double-click `scripts/build_exe.bat`** (or run from a terminal). It will:
   - Install dependencies from `requirements.txt` and PyInstaller
   - Build using `EventFileGenerator.spec`
   - Place the EXE in the `dist` folder

2. **Find your EXE** at: `dist\EventFileGenerator.exe`

## Clean Build

To start fresh (removes `build` and `dist`, keeps the spec file):

1. **Double-click `scripts/build_exe_clean.bat`**

## Manual Build

From the project root (Event File Generator folder):

```bash
pip install -r requirements.txt
pip install pyinstaller
python -m PyInstaller --noconfirm --clean EventFileGenerator.spec
```

The spec file bundles CustomTkinter data so the GUI works in the built EXE. If the onefile build fails at runtime (e.g. missing theme files), use the onedir spec instead:

```bash
python -m PyInstaller --noconfirm --clean EventFileGenerator_onedir.spec
```

Then run `dist\EventFileGenerator\EventFileGenerator.exe` (the output is a folder, not a single file).

## What Gets Created

- **`dist/EventFileGenerator.exe`** - The standalone executable (distribute this)
- **`build/`** - Temporary build files (can be deleted)
- **`EventFileGenerator.spec`** - PyInstaller spec (used by the build scripts; keep it)

## Distributing the EXE

The EXE file in the `dist` folder is completely standalone:
- ✅ No Python installation required
- ✅ No dependencies needed
- ✅ Can run on any Windows 10/11 computer
- ✅ All code is bundled inside

Copy `dist\EventFileGenerator.exe` to any Windows computer and run it.

## Notes

- The first run may take a few seconds to start (extracting bundled files)
- Windows Defender or antivirus may flag it initially (false positive) - this is normal for PyInstaller executables
- The config file (`event_generator_config.json`) will be created next to the EXE when you first use it
- File size will be around 10-15 MB (includes Python runtime)

## Troubleshooting

### "Python is not installed"
- Install Python from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation

### "PyInstaller not found" or "'pyinstaller' is not recognized"
- Run: `pip install pyinstaller`
- Then use: `python -m PyInstaller` instead of just `pyinstaller`

### EXE doesn't start
- Check Windows Defender/Antivirus isn't blocking it
- Try running as Administrator
- Check the build completed without errors

### Large file size
- This is normal - PyInstaller bundles Python and all dependencies
- The `--onefile` option creates a single file for easier distribution
