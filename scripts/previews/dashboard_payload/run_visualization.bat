@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
py visualization\15_build_dashboard_payload\preview_dashboard_payload.py %*
exit /b %ERRORLEVEL%
