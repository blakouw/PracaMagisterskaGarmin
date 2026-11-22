@echo off
setlocal
pushd "%~dp0..\frontend" || exit /b 1
call npm.cmd run build
set "BUILD_CODE=%ERRORLEVEL%"
call npm.cmd test
set "TEST_CODE=%ERRORLEVEL%"
popd
python -B "%~dp0validate_dashboard.py" --build-exit-code %BUILD_CODE% --frontend-test-exit-code %TEST_CODE%
exit /b %ERRORLEVEL%
