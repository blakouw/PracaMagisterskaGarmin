@echo off
setlocal
pushd "%~dp0.." || exit /b 1
python -B -m backend.api_server %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
