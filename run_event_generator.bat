@echo off
echo Starting Event File Generator...
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

REM Run the Python script
python "%~dp0event_folder_generator.py"

if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
