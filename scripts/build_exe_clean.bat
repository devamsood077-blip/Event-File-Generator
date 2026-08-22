@echo off
echo ========================================
echo Clean Build - Event File Generator (EXE)
echo ========================================
echo.

cd /d "%~dp0.."

where py >nul 2>nul && set PY=py || set PY=python
%PY% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install from https://www.python.org/downloads/ and check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo Installing dependencies...
%PY% -m pip install --upgrade pip -q
%PY% -m pip install -r requirements.txt -q
%PY% -m pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Removing previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building with PyInstaller (EventFileGenerator.spec)...
echo.

%PY% -m PyInstaller --noconfirm --clean EventFileGenerator.spec

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Clean build completed successfully.
echo ========================================
echo.
echo Output: dist\EventFileGenerator.exe
echo.
pause
