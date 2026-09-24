@echo off
rem ============================================================
rem  Chengyu Cards - remove the two scheduled tasks
rem ============================================================
schtasks /Delete /TN "ChengyuCard_Start" /F >nul 2>&1
schtasks /Delete /TN "ChengyuCard_Stop" /F >nul 2>&1
echo.
echo   [OK] Scheduled tasks removed.
echo        If the display is on screen right now, press Alt+F4.
echo.
pause
