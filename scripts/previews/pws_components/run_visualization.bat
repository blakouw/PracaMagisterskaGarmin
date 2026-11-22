@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\10_compute_pws_components\preview_pws_components.py %*
exit /b %ERRORLEVEL%
