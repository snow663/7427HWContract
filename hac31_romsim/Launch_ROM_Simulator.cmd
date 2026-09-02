@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel% equ 0 (
    start "7427 ROM Simulator" pyw -3 -m romsim.gui
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "7427 ROM Simulator" pythonw -m romsim.gui
    exit /b 0
)

echo Python 3.10 or newer was not found.
echo Install Python for Windows, then double-click this launcher again.
pause
exit /b 1
