# Building Event File Generator for macOS

This guide explains how to create a standalone macOS application (.app) from the Python script.

## Important: You must build on macOS

**PyInstaller cannot cross-compile.** The Mac build must be run on a Mac (macOS 10.13 or later). You cannot produce a Mac app from Windows or Linux.

- If you have a Mac: use the steps below on that Mac.
- If you don't have a Mac: see [Building without a Mac](#building-without-a-mac-github-actions) below to build using GitHub Actions (free for public repos).

## Prerequisites

- macOS 10.13 (High Sierra) or later
- Python 3.7 or higher installed on your Mac
- Python must be accessible via `python3` command

## Quick Build

1. **Open Terminal** and navigate to the Event File Generator folder:
   ```bash
   cd "/path/to/Event File Generator"
   ```

2. **Make the build script executable** (first time only):
   ```bash
   chmod +x build_mac.sh
   ```

3. **Run the build script**:
   ```bash
   ./build_mac.sh
   ```

4. **Find your app** at: `dist/EventFileGenerator`

## Clean Build

If you want to start fresh (removes old build files):

1. **Make the clean build script executable** (first time only):
   ```bash
   chmod +x build_mac_clean.sh
   ```

2. **Run the clean build script**:
   ```bash
   ./build_mac_clean.sh
   ```

## Manual Build

If you prefer to build manually:

```bash
# Install PyInstaller
pip3 install pyinstaller

# Build the app
python3 -m PyInstaller --onefile --windowed --name "EventFileGenerator" event_folder_generator.py
```

## What Gets Created

- **`dist/EventFileGenerator`** - The standalone macOS application (this is what you distribute)
- **`build/`** - Temporary build files (can be deleted)
- **`EventFileGenerator.spec`** - PyInstaller spec file (can be kept for custom builds)

## Creating a .app Bundle (Optional)

To create a proper macOS .app bundle:

```bash
# After building, create the app bundle
mkdir -p "EventFileGenerator.app/Contents/MacOS"
cp dist/EventFileGenerator "EventFileGenerator.app/Contents/MacOS/EventFileGenerator"
chmod +x "EventFileGenerator.app/Contents/MacOS/EventFileGenerator"

# Create Info.plist
cat > "EventFileGenerator.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>EventFileGenerator</string>
    <key>CFBundleIdentifier</key>
    <string>com.eventfilegenerator.app</string>
    <key>CFBundleName</key>
    <string>Event File Generator</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
```

## Distributing the App

The application in the `dist` folder is standalone:
- ✅ No Python installation required
- ✅ No dependencies needed
- ✅ Can run on any macOS 10.13+ computer
- ✅ All code is bundled inside

Simply copy `EventFileGenerator` (or the `.app` bundle) to any Mac and run it!

## Notes

- The first run may take a few seconds to start (extracting bundled files)
- macOS Gatekeeper may warn about the app - this is normal for PyInstaller apps
- You may need to right-click and select "Open" the first time, then click "Open" in the security dialog
- The config file (`event_generator_config.json`) will be created next to the app when you first use it
- File size will be around 15-20 MB (includes Python runtime)

## Troubleshooting

### "Python 3 is not installed"
- Install Python from [python.org](https://www.python.org/downloads/)
- Or use Homebrew: `brew install python3`

### "PyInstaller not found"
- Run: `pip3 install pyinstaller`
- Then use: `python3 -m PyInstaller` instead of just `pyinstaller`

### App doesn't start / Gatekeeper warning
- Right-click the app and select "Open"
- Click "Open" in the security dialog
- Or go to System Preferences > Security & Privacy and allow the app

### "App is damaged" error
- This is a Gatekeeper issue
- Run: `xattr -cr EventFileGenerator` to remove quarantine attributes
- Or right-click and select "Open" to bypass Gatekeeper

### Large file size
- This is normal - PyInstaller bundles Python and all dependencies
- The `--onefile` option creates a single file for easier distribution

### Build fails with "NONE" or icon error
- The build scripts no longer pass `--icon=NONE` (that was being treated as a filename). If you use an old script, remove the `--icon=NONE` argument.

## Building without a Mac (GitHub Actions)

If you don't have a Mac, you can build the macOS app in the cloud using GitHub Actions:

1. Push this project to a GitHub repository.
2. The workflow in `.github/workflows/build-mac.yml` runs on every push (or you can trigger it manually).
3. When the run finishes, open the **Actions** tab → your workflow run → **Artifacts**.
4. Download **EventFileGenerator-mac** to get the Mac executable.

No Mac required; the build runs on GitHub’s macOS runners.

## Code Signing (Optional, for Distribution)

If you want to distribute the app and avoid Gatekeeper warnings:

1. Get an Apple Developer ID certificate
2. Sign the app:
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" EventFileGenerator
   ```
3. Notarize with Apple (for macOS 10.15+)
