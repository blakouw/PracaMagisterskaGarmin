@echo off
setlocal
pushd "%~dp0..\.."
python "visualization\02_read_xlsx_workbook\preview_workbook_structure.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
