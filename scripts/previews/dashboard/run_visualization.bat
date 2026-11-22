@echo off
setlocal
python -B "%~dp0preview_ui_contract.py" %*
exit /b %ERRORLEVEL%
