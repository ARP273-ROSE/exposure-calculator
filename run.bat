@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

:: ========== Auto-update from GitHub ==========
where git >nul 2>&1
if %ERRORLEVEL%==0 (
    if exist ".git" (
        git pull --ff-only origin main >nul 2>&1
    )
)

:: ========== Check Python ==========
:: Try python in PATH - verify it's real (not Windows Store stub)
set "PYTHON_FOUND="
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
    if !ERRORLEVEL!==0 set "PYTHON_FOUND=1"
)
if defined PYTHON_FOUND goto :run_python

where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
    pythonw -c "import sys" >nul 2>&1
    if !ERRORLEVEL!==0 goto :run_python
)

:: Python not found - try to install via winget
echo.
echo [Exposure Calculator] Python not found. Attempting automatic installation...
echo.

:: ========== Check winget ==========
where winget >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Exposure Calculator] winget not found.
    echo winget is included in Windows 10 1809+ and Windows 11.
    echo.
    echo Installing App Installer ^(includes winget^) from Microsoft Store...
    start ms-windows-store://pdp/?productid=9nblggh4nns1
    echo.
    echo After installing App Installer, close this window and run run.bat again.
    echo Or install Python manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ========== Install Python via winget ==========
echo [Exposure Calculator] Installing Python 3.12 via winget...
echo You may need to accept the UAC prompt ^(administrator rights^).
echo.
winget install --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
if %ERRORLEVEL% neq 0 (
    echo.
    echo [Exposure Calculator] winget installation failed.
    echo Please install Python manually from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [Exposure Calculator] Python installed successfully.
echo Please CLOSE this window and run run.bat AGAIN ^(to refresh PATH^).
pause
exit /b 0

:run_python
:: ========== Run the application ==========
pythonw "%~dp0ExposureCalculator.py"
if errorlevel 1 (
    python "%~dp0ExposureCalculator.py"
    if errorlevel 1 (
        echo.
        echo [Exposure Calculator] Error launching. Press any key to exit...
        pause
        exit /b 1
    )
)
exit /b 0
