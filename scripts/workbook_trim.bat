@echo off
setlocal
pushd "%~dp0..\.."
python "pipeline\03_trim_workbook\main.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%