@echo off
setlocal
cd /d "%~dp0\..\.."
python visualization\12_compute_pws_score\preview_pws_score.py %*
exit /b %ERRORLEVEL%
