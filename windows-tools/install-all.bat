@echo off
setlocal
:: ── Loz Windows Tools — Master Installer ─────────────────────────────────
:: Run this once as Administrator to install everything:
::   • Content Dialog   (Ctrl+Shift+V/W/S — intercept & route captures)
::   • Whisper Hook     (Ctrl+Shift+R hold — voice transcription)
::   • ShareX Hook      (local capture receiver for ShareX)
::   • Hot Corners      (mouse-corner actions)
::   • Right Corner     (slide-in panel on right screen edge)
::   • Hey Claude       (wake-word listener — from voice-listener/)
:: ─────────────────────────────────────────────────────────────────────────

set "TOOLS=%~dp0"

echo.
echo ╔══════════════════════════════════════════╗
echo ║     Loz Windows Tools — Master Setup     ║
echo ╚══════════════════════════════════════════╝
echo.

:: check admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Please right-click this file and "Run as administrator".
    pause & exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found.
    echo Install Python 3.10+ from https://python.org
    echo Make sure to tick "Add Python to PATH" during install.
    pause & exit /b 1
)

echo Installing tools in order. Each step may take a minute.
echo.

:: ── 1. Content Dialog ──────────────────────────────────────────────────
echo [1/6] Content Dialog...
call "%TOOLS%content-dialog\install.bat"
echo.

:: ── 2. Whisper Hook ────────────────────────────────────────────────────
echo [2/6] Whisper Hook...
call "%TOOLS%whisper-hook\install.bat"
echo.

:: ── 3. ShareX Hook ─────────────────────────────────────────────────────
echo [3/6] ShareX Hook...
call "%TOOLS%sharex-hook\install.bat"
echo.

:: ── 4. Hot Corners ─────────────────────────────────────────────────────
echo [4/6] Hot Corners...
call "%TOOLS%hot-corners\install.bat"
echo.

:: ── 5. Right Corner ────────────────────────────────────────────────────
echo [5/6] Right Corner Panel...
call "%TOOLS%right-corner\install.bat"
echo.

:: ── 6. Hey Claude (voice-listener) ─────────────────────────────────────
set "VOICE=%TOOLS%..\voice-listener"
if exist "%VOICE%\install.bat" (
    echo [6/6] Hey Claude wake-word listener...
    call "%VOICE%\install.bat"
) else (
    echo [6/6] Hey Claude: voice-listener folder not found, skipping.
)
echo.

echo.
echo ╔══════════════════════════════════════════╗
echo ║   All tools installed. Reboot or log    ║
echo ║   out / in to activate startup tasks.   ║
echo ╠══════════════════════════════════════════╣
echo ║  Quick reference:                        ║
echo ║   Ctrl+Shift+V  → dialog (clipboard)    ║
echo ║   Ctrl+Shift+W  → dialog (whisper)      ║
echo ║   Ctrl+Shift+S  → dialog (ShareX)       ║
echo ║   Ctrl+Shift+R  → record voice          ║
echo ║   Right edge    → slide-in panel        ║
echo ║   Top-right corner → Claude Desktop     ║
echo ║   Top-left corner  → Gallery            ║
echo ╚══════════════════════════════════════════╝
echo.
pause
