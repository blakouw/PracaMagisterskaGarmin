@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\..\.." >nul
cd pipeline\18_angular_dashboard_ui\app
npm.cmd run build
set "BUILD_CODE=%ERRORLEVEL%"
cd ..\..\..
py pipeline\18_angular_dashboard_ui\validate_ui_contract.py --build-exit-code %BUILD_CODE%
set "VALIDATE_CODE=%ERRORLEVEL%"
popd >nul
if not "%BUILD_CODE%"=="0" exit /b %BUILD_CODE%
exit /b %VALIDATE_CODE%
