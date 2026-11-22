@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\08_compute_load_metrics\preview_load_metrics.py %*
exit /b %ERRORLEVEL%
