@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\05_normalize_daily_records\main.py
exit /b %ERRORLEVEL%
