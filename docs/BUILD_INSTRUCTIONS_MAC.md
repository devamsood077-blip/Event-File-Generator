# Building Event File Generator for macOS

This guide explains how to create a standalone macOS application (.app) from the Python script.

## Important: You must build on macOS

**PyInstaller cannot cross-compile.** The Mac build must be run on a Mac (macOS 10.13 or later). You cannot produce a Mac app from Windows or Linux.

- If you have a Mac: use the steps below on that Mac.
- If you don't have a Mac: see [Building via GitHub Actions](#building-via-github-actions-no-mac-needed) below to build using GitHub (free for public repos).

## Prerequisites

- macOS 10.13 (High Sierra) or later
- Python 3.7 or higher installed on your Mac
- Python must be accessible via `python3` command

## Quick Build

1. **Open Terminal** and go to the project folder:
   ```bash
   cd "/path/to/Event File Generator"
   ```

2. **Make the build script executable** (first time only):
   ```bash
   chmod +x scripts/build_mac.sh
   ```

3. **Run the build**:
   ```bash
   ./scripts/build_mac.sh
   ```
   This installs dependencies from `requirements.txt` and PyInstaller, then builds using `EventFileGenerator.spec`.

4. **Find your app** at: `dist/EventFileGenerator.app`

## Clean Build

If you want to start fresh (removes old build files):

1. **Make the clean build script executable** (first time only):
   ```bash
   chmod +x scripts/build_mac_clean.sh
   ```

2. **Run the clean build script**:
   ```bash
   ./scripts/build_mac_clean.sh
   ```

## Manual Build

From the project root:

```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
python3 -m PyInstaller --noconfirm --clean EventFileGenerator.spec
```

If the onefile build fails at runtime (e.g. CustomTkinter theme not found), use the onedir spec:

```bash
python3 -m PyInstaller --noconfirm --clean EventFileGenerator_onedir.spec
```

Then run `dist/EventFileGenerator.app`.

## What Gets Created

- **`dist/EventFileGenerator.app`** - The double-clickable macOS app (this is what you distribute)
- **`dist/EventFileGenerator`** - The raw one-file binary (inside the `.app` as well)
- **`build/`** - Temporary build files (can be deleted)
- **`EventFileGenerator.spec`** - PyInstaller spec file (used by the build scripts; keep it)

The spec wraps the binary in a `.app` automatically when you build on a Mac. You do not need to create Info.plist by hand.

## Distributing the App

The `.app` in the `dist` folder is standalone:
- No Python installation required
- No extra dependencies needed
- Runs on macOS 10.13+ (Apple Silicon when built on `macos-latest` / a current Mac)
- All code is bundled inside

Copy `EventFileGenerator.app` to any Mac and double-click it.

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

## Building via GitHub Actions (no Mac needed)

You can build the macOS app on GitHub's servers so you don't need a Mac.

### Step 1: Push the project to GitHub

1. Create a new repository on [GitHub](https://github.com/new) (or use an existing one).
2. Make sure the project includes the workflow file: **`.github/workflows/build-mac.yml`**
3. Commit and push everything:
   ```bash
   git add .
   git commit -m "Add Mac build workflow"
   git push origin main
   ```
   (Use your actual branch name if it's not `main` — e.g. `master`.)

### Step 2: Run the build

**Option A — Automatic:** The workflow runs on every push to `main` or `master`. After you push, go to the **Actions** tab and wait for the run to finish.

**Option B — Manual:** On GitHub, open your repo → **Actions** → **Build for macOS** → **Run workflow** → **Run workflow**. This works from any branch.

### Step 3: Download the Mac app

1. In **Actions**, click the completed workflow run (e.g. "Build for macOS").
2. Scroll to **Artifacts** at the bottom.
3. Click **EventFileGenerator-macOS** to download a zip.
4. Unzip it. Inside is **EventFileGenerator.app**. Copy that to a Mac and double-click it.

No Mac required; the build runs on GitHub's macOS runners.

## Code Signing (Optional, for Distribution)

If you want to distribute the app and avoid Gatekeeper warnings:

1. Get an Apple Developer ID certificate
2. Sign the app:
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" EventFileGenerator
   ```
3. Notarize with Apple (for macOS 10.15+)
