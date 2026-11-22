@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\07_build_daily_features\preview_daily_features.py %*
exit /b %ERRORLEVEL%
