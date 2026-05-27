@echo off
chcp 936 >nul 2>&1

:: Check admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo ========================================
echo TikTok Publisher - Install
echo ========================================
echo.

set "INSTALL_DIR=%ProgramFiles%\TikTokPublisher"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\TikTokPublisher"

:: Check if already installed
if exist "%INSTALL_DIR%\TikTokPublisherWeb.exe" (
    echo Old version detected, closing...
    taskkill /F /IM TikTokPublisherWeb.exe >nul 2>&1
    timeout /t 2 >nul
)

echo [1/5] Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\web" mkdir "%INSTALL_DIR%\web"
if not exist "%INSTALL_DIR%\web\templates" mkdir "%INSTALL_DIR%\web\templates"
if not exist "%INSTALL_DIR%\web\static" mkdir "%INSTALL_DIR%\web\static"
if not exist "%INSTALL_DIR%\web\static\css" mkdir "%INSTALL_DIR%\web\static\css"
if not exist "%INSTALL_DIR%\web\static\js" mkdir "%INSTALL_DIR%\web\static\js"
echo Done

echo.
echo [2/5] Copying files...
if exist "dist\TikTokPublisherWeb.exe" (
    copy /Y "dist\TikTokPublisherWeb.exe" "%INSTALL_DIR%\" >nul
) else (
    echo ERROR: dist\TikTokPublisherWeb.exe not found
    echo Please run build_web.bat first
    pause
    exit /b 1
)

if exist "dist\web\templates" (
    xcopy /E /Y "dist\web\templates\*" "%INSTALL_DIR%\web\templates\" >nul
)
if exist "dist\web\static" (
    xcopy /E /Y "dist\web\static\*" "%INSTALL_DIR%\web\static\" >nul
)
if exist "dist\icon.ico" (
    copy /Y "dist\icon.ico" "%INSTALL_DIR%\" >nul
)
echo Done

echo.
echo [3/5] Creating shortcuts...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP_DIR%\TikTok Publisher.lnk'); $s.TargetPath = '%INSTALL_DIR%\TikTokPublisherWeb.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

if not exist "%START_MENU%" mkdir "%START_MENU%"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\TikTok Publisher.lnk'); $s.TargetPath = '%INSTALL_DIR%\TikTokPublisherWeb.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"
echo Done

echo.
echo [4/5] Setting auto-start...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "TikTokPublisher" /t REG_SZ /d "\"%INSTALL_DIR%\TikTokPublisherWeb.exe\"" /f >nul
echo Done

echo.
echo [5/5] Creating uninstaller...
(
echo @echo off
echo chcp 936 ^>nul 2^>^&1
echo.
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo Please run as Administrator!
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Uninstalling TikTok Publisher...
echo taskkill /F /IM TikTokPublisherWeb.exe ^>nul 2^>^&1
echo timeout /t 2 ^>nul
echo reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "TikTokPublisher" /f ^>nul 2^>^&1
echo del /f /q "%%USERPROFILE%%\Desktop\TikTok Publisher.lnk" ^>nul 2^>^&1
echo rmdir /s /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TikTokPublisher" ^>nul 2^>^&1
echo cd /d "%%TEMP%%"
echo rmdir /s /q "%INSTALL_DIR%" 2^>nul
echo echo Uninstall complete!
echo pause
) > "%INSTALL_DIR%\uninstall.bat"
echo Done

echo.
echo ========================================
echo INSTALL SUCCESS!
echo.
echo Install location: %INSTALL_DIR%
echo.
echo Created:
echo   - Desktop shortcut
echo   - Start menu shortcut
echo   - Auto-start on boot
echo   - Uninstaller
echo.
echo Start now?
choice /c YN /m "Y=Yes, N=No"
if errorlevel 1 (
    start "" "%INSTALL_DIR%\TikTokPublisherWeb.exe"
)

pause
