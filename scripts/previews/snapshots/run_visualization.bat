@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
py visualization\16_persist_local_snapshot\preview_dashboard_snapshot.py %*
exit /b %ERRORLEVEL%
