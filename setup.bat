@echo off
setlocal

title Velo Booster Setup
:: === CONFIGURATION ===
set PYTHON_VERSION=3.12.3
set INSTALLER=python-installer.exe
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set PYTHON_DIR=C:\Python312

:: === STEP 1: Download Python Installer ===
echo === Downloading Python %PYTHON_VERSION% installer... ===
curl -L -o %INSTALLER% %PYTHON_URL%

:: === STEP 2: Install Python Silently with PATH and pip ===
echo === Installing Python silently... ===
%INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1 InstallLauncherAllUsers=1 TargetDir="%PYTHON_DIR%"

:: === STEP 3: Wait to ensure environment updates ===
timeout /t 10 >nul

:: === STEP 4: Create pip install script ===
set PIP_INSTALLER=pip_install.bat

echo === Creating pip install script... ===
(
    echo @echo off
    echo "%PYTHON_DIR%\python.exe" -m pip install --upgrade pip
    echo "%PYTHON_DIR%\python.exe" -m pip install pypiwin32 pillow opencv-python
) > %PIP_INSTALLER%

:: === STEP 5: Run pip install script ===
echo === Installing Python packages... ===
call %PIP_INSTALLER%

:: === STEP 6: Cleanup ===
echo === Cleaning up installer files... ===
del %INSTALLER% >nul 2>&1
del %PIP_INSTALLER% >nul 2>&1

echo === Done! Python and packages installed successfully ===
pause
