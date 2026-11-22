@echo off
setlocal
cd /d "%~dp0\..\.."
python pipeline\12_compute_pws_score\main.py
exit /b %ERRORLEVEL%
