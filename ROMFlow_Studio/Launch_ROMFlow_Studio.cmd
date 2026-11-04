@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (py -3 -m studio.server %*) else (python -m studio.server %*)
pause
