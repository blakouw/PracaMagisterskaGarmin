@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\07_build_daily_features\main.py
exit /b %ERRORLEVEL%
