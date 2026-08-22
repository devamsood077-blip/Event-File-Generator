#!/bin/bash
# Clean build of Event File Generator for macOS. Run on a Mac.

set -e
cd "$(dirname "$0")/.."

echo "========================================"
echo "Clean Build - Event File Generator (macOS)"
echo "========================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH."
    echo "Install from https://www.python.org/downloads/ or: brew install python3"
    echo ""
    exit 1
fi

echo "Installing dependencies..."
python3 -m pip install --upgrade pip -q
python3 -m pip install -r requirements.txt -q
python3 -m pip install pyinstaller -q

echo ""
echo "Removing previous build artifacts..."
rm -rf build dist

echo ""
echo "Building with PyInstaller (EventFileGenerator.spec)..."
echo ""

python3 -m PyInstaller --noconfirm --clean EventFileGenerator.spec

echo ""
echo "========================================"
echo "Clean build completed successfully."
echo "========================================"
echo ""
echo "Output: dist/EventFileGenerator.app"
echo "       (also dist/EventFileGenerator — the raw binary)"
echo ""
