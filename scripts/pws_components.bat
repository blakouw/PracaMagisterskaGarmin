@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\10_compute_pws_components\main.py
exit /b %ERRORLEVEL%
