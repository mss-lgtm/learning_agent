@echo off
chcp 936 >nul 2>&1

echo ========================================
echo TikTok Publisher - Create Installer
echo ========================================
echo.

echo [1/3] Building program...
call build_web.bat
if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

echo.
echo [2/3] Checking Inno Setup...
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo.
    echo Inno Setup 6 not found!
    echo.
    echo Please install Inno Setup 6:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo Or run: installer\download_inno.ps1
    echo.
    pause
    exit /b 1
)

echo Inno Setup found: %ISCC%

echo.
echo [3/3] Creating installer...
if not exist "dist\installer" mkdir "dist\installer"
"%ISCC%" installer\setup.iss

if errorlevel 1 (
    echo ERROR: Failed to create installer
    pause
    exit /b 1
)

echo.
echo ========================================
echo INSTALLER CREATED!
echo.
echo Output: dist\installer\TikTokPublisher_Setup_1.0.0.exe
echo ========================================
echo.

explorer dist\installer
pause
