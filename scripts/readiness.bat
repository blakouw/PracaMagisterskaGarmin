@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\09_compute_readiness\main.py
exit /b %ERRORLEVEL%
