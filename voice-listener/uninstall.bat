@echo off
set "DIR=%~dp0"
set "TASK_NAME=HeyClaude"

echo Removing Hey Claude...

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
taskkill /IM hey_claude.exe /F >nul 2>&1

if exist "%DIR%.venv" (
    rmdir /S /Q "%DIR%.venv"
)

echo Done. Hey Claude has been removed.
pause
