@echo off
echo ===================================================
echo Velo Booster - Starting GUI
echo ===================================================
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please run setup.bat first to install Python and required packages.
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

:: Run the GUI application
echo Starting Velo Booster...
start pythonw gui.py

exit
