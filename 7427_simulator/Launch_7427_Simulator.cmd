@echo off
cd /d "%~dp0"
py -3 -m sim7427
if errorlevel 1 pause
