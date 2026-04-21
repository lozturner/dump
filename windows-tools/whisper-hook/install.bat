@echo off
setlocal

:: ── Whisper Hook installer ────────────────────────────────────────────────
:: Installs openai-whisper and registers a startup task.
:: First run downloads the Whisper model (~150 MB for base.en).
:: ─────────────────────────────────────────────────────────────────────────

set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "TASK=LozWhisperHook"

echo.
echo === Loz Whisper Hook Installer ===
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause & exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv "%VENV%"
if %errorlevel% neq 0 ( echo ERROR: venv failed. & pause & exit /b 1 )

echo [2/4] Installing dependencies (whisper download ~150 MB first run)...
"%VENV%\Scripts\pip" install --quiet --upgrade pip
"%VENV%\Scripts\pip" install --quiet -r "%DIR%requirements.txt"
if %errorlevel% neq 0 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo [3/4] Pre-downloading Whisper model...
"%PYTHON%" -c "import whisper; whisper.load_model('base.en')"
if %errorlevel% neq 0 ( echo WARNING: model pre-download failed -- will download on first use. )

echo [4/4] Registering startup task...
schtasks /Delete /TN "%TASK%" /F >nul 2>&1
schtasks /Create ^
  /TN "%TASK%" ^
  /TR "\"%PYTHON%\" \"%DIR%whisper_hook.py\"" ^
  /SC ONLOGON ^
  /DELAY 0001:30 ^
  /RL HIGHEST ^
  /F >nul

if %errorlevel% neq 0 (
    echo ERROR: Task Scheduler registration failed. Run as Administrator?
    pause & exit /b 1
)

echo.
echo =============================================
echo  Whisper Hook installed.
echo  Hold Ctrl+Shift+R to record, release to
echo  transcribe. Result appears in content-dialog.
echo  Edit whisper_config.json to change settings.
echo =============================================
echo.
echo  To start right now:
echo  "%PYTHON%" "%DIR%whisper_hook.py"
echo.
pause
