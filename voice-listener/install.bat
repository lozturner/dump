@echo off
setlocal

:: ── Hey Claude installer ──────────────────────────────────────────────────
:: Run this once as Administrator.
:: It will:
::   1. Create a Python venv and install dependencies
::   2. Train the custom "hey claude" wake word model (5-10 min, one-time)
::   3. Register the listener to run at Windows login via Task Scheduler
:: ─────────────────────────────────────────────────────────────────────────

set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK_NAME=HeyClaude"

echo.
echo === Hey Claude Installer ===
echo.

:: Check Python exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Create venv
echo [1/4] Creating virtual environment...
python -m venv "%VENV%"
if %errorlevel% neq 0 ( echo ERROR: venv creation failed. & pause & exit /b 1 )

:: Install deps
echo [2/4] Installing dependencies...
"%VENV%\Scripts\pip" install --quiet --upgrade pip
"%VENV%\Scripts\pip" install --quiet -r "%DIR%requirements.txt"
if %errorlevel% neq 0 ( echo ERROR: pip install failed. & pause & exit /b 1 )

:: Train wake word model (skip if already trained)
if exist "%DIR%models\hey_claude.onnx" (
    echo [3/4] Custom model already trained — skipping.
) else (
    echo [3/4] Training "hey claude" wake word model...
    echo       This takes 5-10 minutes. Go make a cup of tea.
    echo.
    "%PYTHON%" "%DIR%train_model.py"
    if %errorlevel% neq 0 ( echo ERROR: model training failed. & pause & exit /b 1 )
)

:: Register with Task Scheduler
echo [4/4] Registering startup task...

:: Remove old task if it exists
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

:: Create new task: runs at login, highest privilege, 1-minute startup delay
schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%PYTHON%\" \"%DIR%hey_claude.py\"" ^
  /SC ONLOGON ^
  /DELAY 0001:00 ^
  /RL HIGHEST ^
  /F >nul

if %errorlevel% neq 0 (
    echo ERROR: Could not register task. Are you running as Administrator?
    pause
    exit /b 1
)

echo.
echo =========================================
echo  Done! Hey Claude is installed.
echo  Say "Hey Claude" after your next login.
echo =========================================
echo.
echo  To start right now without rebooting:
echo  "%PYTHON%" "%DIR%hey_claude.py"
echo.
echo  To uninstall: run uninstall.bat
echo.
pause
