@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\06_normalize_activities\main.py
exit /b %ERRORLEVEL%
