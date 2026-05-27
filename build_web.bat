@echo off
chcp 936 >nul 2>&1

echo ========================================
echo TikTok Publisher - Web Build
echo ========================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo Python OK

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies OK

echo.
echo [3/4] Creating icon...
if not exist "assets" mkdir "assets"
python create_icon.py
echo Icon OK

echo.
echo [4/4] Building with PyInstaller...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

pyinstaller --onefile --noconsole --name TikTokPublisherWeb --icon assets/icon.ico --add-data "web/templates;web/templates" --add-data "web/static;web/static" run_web.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Copying web resources...
if not exist "dist\web\templates" mkdir "dist\web\templates"
if not exist "dist\web\static" mkdir "dist\web\static"
xcopy /E /Y "web\templates\*" "dist\web\templates\" >nul
xcopy /E /Y "web\static\*" "dist\web\static\" >nul
copy /Y "assets\icon.ico" "dist\" >nul 2>&1

echo.
echo ========================================
echo BUILD SUCCESS!
echo.
echo Output: dist\TikTokPublisherWeb.exe
echo ========================================
echo.

explorer dist
pause
