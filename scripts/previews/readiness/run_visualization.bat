@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\09_compute_readiness\preview_readiness.py %*
exit /b %ERRORLEVEL%
