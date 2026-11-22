@echo off
setlocal
pushd "%~dp0..\.."
python "pipeline\02_read_xlsx_workbook\main.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
