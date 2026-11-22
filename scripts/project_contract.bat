@echo off
setlocal
pushd "%~dp0..\.."
python "pipeline\00_project_contract\main.py"
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
