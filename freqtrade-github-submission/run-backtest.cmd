@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-backtest.ps1"
set "BACKTEST_EXIT=%errorlevel%"
pause
exit /b %BACKTEST_EXIT%
