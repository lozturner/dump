@echo off
setlocal

:: ── Content Dialog installer ──────────────────────────────────────────────
:: Run once as Administrator.
:: Creates a venv, installs deps, registers a startup task.
:: ─────────────────────────────────────────────────────────────────────────

set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK=LozContentDialog"

echo.
echo === Loz Content Dialog Installer ===
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause & exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv "%VENV%"
if %errorlevel% neq 0 ( echo ERROR: venv failed. & pause & exit /b 1 )

echo [2/3] Installing dependencies...
"%VENV%\Scripts\pip" install --quiet --upgrade pip
"%VENV%\Scripts\pip" install --quiet -r "%DIR%requirements.txt"
if %errorlevel% neq 0 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo [3/3] Registering startup task...
schtasks /Delete /TN "%TASK%" /F >nul 2>&1
schtasks /Create ^
  /TN "%TASK%" ^
  /TR "\"%PYTHON%\" \"%DIR%content_dialog.py\"" ^
  /SC ONLOGON ^
  /DELAY 0001:00 ^
  /RL HIGHEST ^
  /F >nul

if %errorlevel% neq 0 (
    echo ERROR: Task Scheduler registration failed. Are you running as Administrator?
    pause & exit /b 1
)

echo.
echo =============================================
echo  Content Dialog installed.
echo  Hotkeys (after next login):
echo    Ctrl+Shift+V  — open with clipboard
echo    Ctrl+Shift+W  — open with Whisper transcript
echo    Ctrl+Shift+S  — open with ShareX capture
echo  Edit mcp_destinations.json to configure.
echo =============================================
echo.
echo  To start right now:
echo  "%PYTHON%" "%DIR%content_dialog.py"
echo.
pause
