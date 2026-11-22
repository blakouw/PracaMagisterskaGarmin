@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\06_normalize_activities\preview_activities.py %*
exit /b %ERRORLEVEL%
