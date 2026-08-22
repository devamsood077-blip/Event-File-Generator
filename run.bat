@echo off
cd /d "%~dp0"

REM Use py (Python Launcher) if python is not in PATH
where py >nul 2>nul && set PY=py || set PY=python

echo Installing dependencies...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting Event File Generator...
%PY% event_folder_generator.py
if errorlevel 1 (
    echo Script exited with an error.
    pause
    exit /b 1
)

pause
