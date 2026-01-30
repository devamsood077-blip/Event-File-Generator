#!/bin/bash

echo "========================================"
echo "Building Event File Generator for macOS"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH!"
    echo ""
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo "or using Homebrew: brew install python3"
    echo ""
    exit 1
fi

echo "Installing PyInstaller if needed..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install pyinstaller > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PyInstaller"
    exit 1
fi

echo ""
echo "Building macOS application..."
echo ""

# Build the macOS app (no --icon so PyInstaller doesn't look for a file named "NONE")
python3 -m PyInstaller --onefile \
    --windowed \
    --name "EventFileGenerator" \
    event_folder_generator.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "The application is located at:"
echo "dist/EventFileGenerator"
echo ""
echo "You can now distribute this application to any macOS computer"
echo "without requiring Python to be installed."
echo ""
