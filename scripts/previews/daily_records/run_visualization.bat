@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\05_normalize_daily_records\preview_daily_records.py %*
exit /b %ERRORLEVEL%
