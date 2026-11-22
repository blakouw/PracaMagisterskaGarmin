@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\04_garmin_activity_ingest\preview_activity_ingest.py %*
exit /b %ERRORLEVEL%
