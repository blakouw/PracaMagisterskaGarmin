@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\..\.." >nul
cd pipeline\18_angular_dashboard_ui\app
npm.cmd run dev -- --host 127.0.0.1 --port 5173 %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
