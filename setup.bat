@echo off
echo ===================================================
echo Velo Booster - Automated Setup
echo ===================================================
echo.

:: Check if Python is already installed
python --version > nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
) else (
    echo Python is not installed. Installing Python...
    echo.
    
    :: Download Python installer
    echo Downloading Python installer...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'}"
    
    if exist python_installer.exe (
        echo Download complete.
        echo.
        echo Installing Python...
        :: Install Python with required options (add to PATH)
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        :: Wait for installation to complete
        timeout /t 10 /nobreak > nul
        
        :: Clean up installer
        del python_installer.exe
        
        echo Python installation completed.
    ) else (
        echo Failed to download Python installer.
        echo Please install Python manually from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

echo.
echo ===================================================
echo Installing required packages...
echo ===================================================

:: Ensure pip is up to date
python -m pip install --upgrade pip

:: Install required packages from requirements.txt if it exists
if exist requirements.txt (
    echo Installing packages from requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found. Installing packages individually...
    python -m pip install pypiwin32 pillow opencv-python pyside6 requests numpy
)

echo.
echo ===================================================
echo Setup completed successfully!
echo ===================================================
echo.
echo You can now run the bot using:
echo   - GUI Mode: python gui.py
echo.
echo Make sure to:
echo   1. Set Call of Duty: Warzone to English language
echo   2. Configure the game to run in Windowed mode
echo   3. Ensure the "Jump" button is bound to SPACE
echo.
echo Press any key to exit...
pause > nul
