@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\11_compute_pws_weights\main.py
exit /b %ERRORLEVEL%
