@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\11_compute_pws_weights\preview_pws_weights.py %*
exit /b %ERRORLEVEL%
