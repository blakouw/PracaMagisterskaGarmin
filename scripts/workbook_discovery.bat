@echo off
setlocal
pushd "%~dp0..\.."
python "pipeline\01_find_input_workbook\main.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
