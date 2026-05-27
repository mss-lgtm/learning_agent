@echo off
chcp 936 >nul 2>&1

echo ========================================
echo TikTok Publisher - Full Build
echo ========================================
echo.

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo Python OK

echo.
echo [2/5] Installing dependencies...
pip install -r requirements.txt -q
echo Dependencies OK

echo.
echo [3/5] Creating icon...
if not exist "assets" mkdir "assets"
python create_icon.py
echo Icon OK

echo.
echo [4/5] Building with PyInstaller...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

pyinstaller --onefile --noconsole --name TikTokPublisherWeb --icon assets/icon.ico --add-data "web/templates;web/templates" --add-data "web/static;web/static" run_web.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [5/5] Copying resources...
if not exist "dist\web\templates" mkdir "dist\web\templates"
if not exist "dist\web\static" mkdir "dist\web\static"
xcopy /E /Y "web\templates\*" "dist\web\templates\" >nul
xcopy /E /Y "web\static\*" "dist\web\static\" >nul
copy /Y "assets\icon.ico" "dist\" >nul 2>&1

echo.
echo ========================================
echo BUILD SUCCESS!
echo.
echo Output files:
echo   - dist\TikTokPublisherWeb.exe
echo   - dist\web\ (web resources)
echo.
echo To create installer:
echo   Run build_installer.bat (requires Inno Setup)
echo   Or run installer\install_simple.bat (as Admin)
echo ========================================
echo.

explorer dist
pause
