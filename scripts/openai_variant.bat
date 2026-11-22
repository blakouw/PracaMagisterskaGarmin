@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
py pipeline\13_validate_llm_weight_influence\openai_variant.py %*
exit /b %ERRORLEVEL%
