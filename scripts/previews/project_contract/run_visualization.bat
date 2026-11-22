@echo off
setlocal
pushd "%~dp0..\.."
python "visualization\00_project_contract\preview_contract.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
