@echo off
echo ========================================
echo Clean Build of Event File Generator EXE
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Installing PyInstaller if needed...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install pyinstaller >nul 2>&1

if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Cleaning previous build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist EventFileGenerator.spec del /q EventFileGenerator.spec

echo.
echo Building EXE file...
echo.

REM Build the EXE
python -m PyInstaller --onefile ^
    --windowed ^
    --name "EventFileGenerator" ^
    --icon=NONE ^
    --clean ^
    event_folder_generator.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The EXE file is located at:
echo dist\EventFolderGenerator.exe
echo.
echo You can now distribute this EXE file to any Windows computer
echo without requiring Python to be installed.
echo.
pause
