@echo off
setlocal
pushd "%~dp0..\.."
python -m pytest tests\01_find_input_workbook -q
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
