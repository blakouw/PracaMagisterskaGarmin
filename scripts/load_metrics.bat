@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\08_compute_load_metrics\main.py
exit /b %ERRORLEVEL%
