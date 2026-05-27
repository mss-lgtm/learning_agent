@echo off
chcp 936 >nul 2>&1

echo Opening help document...
start "" "%~dp0quick_start.html"

echo.
echo If browser did not open, double-click:
echo %~dp0quick_start.html
echo.
timeout /t 3 >nul
