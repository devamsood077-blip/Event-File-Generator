# Event File Generator

This folder contains all files for the Event File Generator application, organized as follows.

## Folder structure

```
Event File Generator/
├── event_folder_generator.py   # Main application (source)
├── requirements.txt             # Python dependencies (PyInstaller)
├── EventFileGenerator.spec      # PyInstaller spec (optional)
├── event_generator_config.json  # Saved settings (created on first run)
├── README.md                    # This file
├── docs/                        # Documentation
│   ├── BUILD_INSTRUCTIONS.md    # How to build the Windows EXE
│   ├── BUILD_INSTRUCTIONS_MAC.md # How to build the macOS app
│   ├── EVENT_GENERATOR_README.md # User guide
│   └── THEME_COLORS.md          # Theme/color reference
├── scripts/                     # Build and run scripts
│   ├── build_exe.bat            # Build Windows EXE
│   ├── build_exe_clean.bat      # Clean build (Windows)
│   ├── build_mac.sh             # Build macOS app
│   ├── build_mac_clean.sh       # Clean build (macOS)
│   └── run_event_generator.bat  # Run from source (Windows)
├── dist/                        # Built executables (after build)
└── build/                       # PyInstaller cache (can delete)
```

## Quick start

### Windows

- **Run from source:** Double-click `scripts/run_event_generator.bat` or run `python event_folder_generator.py` from this folder.
- **Build EXE:** Double-click `scripts/build_exe.bat`. The EXE will be in `dist/EventFileGenerator.exe`.
- **Use pre-built EXE:** Run `dist/EventFileGenerator.exe` (no Python needed).

### macOS

- **Run from source:** From this folder, run `python3 event_folder_generator.py`.
- **Build app:** From this folder, run `chmod +x scripts/build_mac.sh` (once), then `./scripts/build_mac.sh`. The app will be in `dist/EventFileGenerator.app`.
- **No Mac?** Push the repo to GitHub and run **Actions → Build for macOS**. Download the `EventFileGenerator-macOS` artifact.

## Documentation

- **User guide:** `docs/EVENT_GENERATOR_README.md`
- **Windows build:** `docs/BUILD_INSTRUCTIONS.md`
- **macOS build:** `docs/BUILD_INSTRUCTIONS_MAC.md`
- **Theme/colors:** `docs/THEME_COLORS.md`

## Distribution

- **Windows:** Copy `dist/EventFileGenerator.exe` (and optionally `dist/event_generator_config.json`) to any Windows PC.
- **macOS:** Copy `dist/EventFileGenerator.app` to any Mac (right-click → Open the first time if Gatekeeper warns).

## Notes

- Config file `event_generator_config.json` is created automatically on first run.
- Build scripts in `scripts/` change to the app root automatically; run them from anywhere or double-click them.
