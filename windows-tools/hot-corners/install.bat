@echo off
setlocal

:: ── Hot Corners installer ─────────────────────────────────────────────────
set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK=LozHotCorners"

echo.
echo === Loz Hot Corners Installer ===
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
  /TR "\"%PYTHON%\" \"%DIR%hot_corners.py\"" ^
  /SC ONLOGON ^
  /DELAY 0000:45 ^
  /RL HIGHEST ^
  /F >nul

if %errorlevel% neq 0 (
    echo ERROR: Task Scheduler registration failed. Run as Administrator?
    pause & exit /b 1
)

echo.
echo =============================================
echo  Hot Corners installed.
echo  Corner actions (edit config.json to change):
echo    Top-left      — open Gallery in browser
echo    Top-right     — bring Claude Desktop
echo    Bottom-left   — (none)
echo    Bottom-right  — open Content Dialog
echo =============================================
echo.
echo  To start right now:
echo  "%PYTHON%" "%DIR%hot_corners.py"
echo.
pause
