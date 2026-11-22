@echo off
setlocal
pushd "%~dp0..\.."
python "visualization\03_trim_workbook\preview_trim_report.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%