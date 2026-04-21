@echo off
setlocal

:: ── ShareX Hook installer ─────────────────────────────────────────────────
:: Sets up the local capture receiver and registers the ShareX custom uploader.
set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK=LozShareXHook"

echo.
echo === Loz ShareX Hook Installer ===
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
if %errorlevel% neq 0 ( echo ERROR: pip upgrade failed. & pause & exit /b 1 )

echo [3/3] Registering startup task...
schtasks /Delete /TN "%TASK%" /F >nul 2>&1
schtasks /Create ^
  /TN "%TASK%" ^
  /TR "\"%PYTHON%\" \"%DIR%sharex_hook.py\"" ^
  /SC ONLOGON ^
  /DELAY 0001:00 ^
  /RL HIGHEST ^
  /F >nul

if %errorlevel% neq 0 (
    echo ERROR: Task Scheduler registration failed. Run as Administrator?
    pause & exit /b 1
)

echo.
echo =============================================
echo  ShareX Hook installed.
echo.
echo  NEXT STEP: Import the ShareX uploader config
echo  1. Open ShareX
echo  2. Destinations ^> Custom uploader settings
echo  3. Import: sharex_uploader.json (in this folder)
echo  4. Set as active image destination
echo.
echo  Captures will pop up in Content Dialog.
echo =============================================
echo.
echo  To start right now:
echo  "%PYTHON%" "%DIR%sharex_hook.py"
echo.
pause
