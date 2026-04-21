@echo off
setlocal

:: ── Right Corner Panel installer ──────────────────────────────────────────
set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK=LozRightCorner"

echo.
echo === Loz Right Corner Panel Installer ===
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
  /TR "\"%PYTHON%\" \"%DIR%right_corner.py\"" ^
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
echo  Right Corner Panel installed.
echo  Move your mouse to the right screen edge
echo  to reveal the quick-access strip.
echo  Edit right_corner_config.json to customise.
echo =============================================
echo.
echo  To start right now:
echo  "%PYTHON%" "%DIR%right_corner.py"
echo.
pause
