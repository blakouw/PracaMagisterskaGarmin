@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\04_garmin_activity_ingest\main.py
exit /b %ERRORLEVEL%
