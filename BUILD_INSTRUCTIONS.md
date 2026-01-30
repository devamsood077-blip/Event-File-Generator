# Building Event File Generator as EXE

This guide explains how to create a standalone Windows executable (.exe) file from the Python script.

## Prerequisites

- Python 3.7 or higher installed on your Windows system
- Python must be added to your system PATH

## Quick Build

1. **Double-click `build_exe.bat`** - This will:
   - Install PyInstaller if needed
   - Build the EXE file
   - Place it in the `dist` folder

2. **Find your EXE** at: `dist\EventFolderGenerator.exe`

## Clean Build

If you want to start fresh (removes old build files):

1. **Double-click `build_exe_clean.bat`**

## Manual Build

If you prefer to build manually:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the EXE
python -m PyInstaller --onefile --windowed --name "EventFileGenerator" event_folder_generator.py
```

## What Gets Created

- **`dist/EventFolderGenerator.exe`** - The standalone executable (this is what you distribute)
- **`build/`** - Temporary build files (can be deleted)
- **`EventFolderGenerator.spec`** - PyInstaller spec file (can be kept for custom builds)

## Distributing the EXE

The EXE file in the `dist` folder is completely standalone:
- ✅ No Python installation required
- ✅ No dependencies needed
- ✅ Can run on any Windows 10/11 computer
- ✅ All code is bundled inside

Simply copy `EventFileGenerator.exe` to any Windows computer and run it!

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
