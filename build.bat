@echo off
:: Build ExposureCalculator.exe — single-file Windows executable
:: Requirements: pip install pyinstaller pillow matplotlib

echo [build] Building ExposureCalculator.exe ...

:: Clean previous build
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist ExposureCalculator.spec del ExposureCalculator.spec

:: Run PyInstaller (use python -m to avoid PATH issues)
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "ExposureCalculator" ^
    --icon "logo-expo.ico" ^
    --add-data "logo-expo.png;." ^
    --add-data "logo-expo.ico;." ^
    --hidden-import "matplotlib" ^
    --hidden-import "matplotlib.backends.backend_tkagg" ^
    --noupx ^
    ExposureCalculator.py

if %ERRORLEVEL% NEQ 0 (
    echo [build] ERROR: PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo [build] SUCCESS: dist\ExposureCalculator.exe
echo [build] Size:
for %%A in (dist\ExposureCalculator.exe) do echo         %%~zA bytes (%%~A)
echo.
pause
