# Event File Generator - Complete Package

This folder contains all files for the Event File Generator application.

## Contents

### Executable (Ready to Use)
- **`dist/EventFileGenerator.exe`** - Standalone Windows executable (no Python required)
- **`dist/event_generator_config.json`** - Configuration file (created automatically)

### Source Code
- **`event_folder_generator.py`** - Main Python application source code

### Build Scripts (Windows)
- **`build_exe.bat`** - Build the EXE from source
- **`build_exe_clean.bat`** - Clean build (removes old files first)
- **`run_event_generator.bat`** - Run the Python script directly (requires Python)

### Build Scripts (macOS)
- **`build_mac.sh`** - Build the macOS app from source
- **`build_mac_clean.sh`** - Clean build for macOS (removes old files first)

### Configuration
- **`EventFileGenerator.spec`** - PyInstaller build specification
- **`requirements.txt`** - Python dependencies (only PyInstaller needed)

### Documentation
- **`EVENT_GENERATOR_README.md`** - User guide and instructions
- **`BUILD_INSTRUCTIONS.md`** - How to build the Windows EXE from source
- **`BUILD_INSTRUCTIONS_MAC.md`** - How to build the macOS app from source
- **`THEME_COLORS.md`** - Color customization reference

## Quick Start

### Windows Users

#### Option 1: Use the Pre-built EXE (Recommended)
1. Navigate to the `dist` folder
2. Double-click `EventFileGenerator.exe`
3. No Python installation required!

#### Option 2: Run from Source
1. Make sure Python 3.7+ is installed
2. Double-click `run_event_generator.bat`
3. Or run: `python event_folder_generator.py`

#### Option 3: Rebuild the EXE
1. Double-click `build_exe.bat`
2. Wait for build to complete
3. Find the new EXE in `dist/EventFileGenerator.exe`

### macOS Users

#### Option 1: Run from Source
1. Make sure Python 3.7+ is installed (`python3 --version`)
2. Open Terminal and navigate to this folder
3. Run: `python3 event_folder_generator.py`

#### Option 2: Build macOS App
1. Open Terminal and navigate to this folder
2. Make script executable: `chmod +x build_mac.sh`
3. Run: `./build_mac.sh`
4. Find the app at: `dist/EventFileGenerator`

## Distribution

### Windows
- Copy the entire `dist` folder to any Windows computer
- Users can run `EventFileGenerator.exe` directly
- No additional files or installations needed

### macOS
- Copy `dist/EventFileGenerator` to any Mac
- Users can run it directly (may need to right-click and "Open" first time due to Gatekeeper)
- No additional files or installations needed

## Notes

- The config file (`event_generator_config.json`) will be created automatically when you first run the application
- Settings are saved between sessions
- The EXE is completely standalone - no Python or dependencies required
