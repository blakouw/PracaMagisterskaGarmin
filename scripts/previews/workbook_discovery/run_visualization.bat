@echo off
setlocal
pushd "%~dp0..\.."
python "visualization\01_find_input_workbook\preview_workbook_manifest.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
