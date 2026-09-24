@echo off
rem ============================================================
rem  Chengyu Cards - install the two scheduled tasks
rem  Run this ONCE on the classroom PC. Just double-click it.
rem
rem  Uses schtasks.exe, a built-in Windows program, so it is NOT
rem  affected by the PowerShell execution policy.
rem ============================================================
setlocal

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

echo.
echo  ============================================
echo   Chengyu Cards - installing scheduled tasks
echo  ============================================
echo.
echo   Folder: %HERE%
echo.

if not exist "%HERE%\start-player.bat" (
  echo   [x] start-player.bat was not found in this folder.
  echo       Please copy the whole folder, not just install.bat
  echo.
  pause
  exit /b 1
)
if not exist "%HERE%\stop-player.bat" (
  echo   [x] stop-player.bat was not found in this folder.
  echo       Please copy the whole folder, not just install.bat
  echo.
  pause
  exit /b 1
)

schtasks /Create /TN "ChengyuCard_Start" /TR "\"%HERE%\start-player.bat\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 07:30 /F
if errorlevel 1 goto failed

schtasks /Create /TN "ChengyuCard_Stop" /TR "\"%HERE%\stop-player.bat\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:30 /F
if errorlevel 1 goto failed

echo.
echo   [OK] Installed. Two tasks now exist:
echo.
echo        ChengyuCard_Start    Mon-Fri  07:30
echo        ChengyuCard_Stop     Mon-Fri  08:30
echo.
echo   Next: double-click  test-now.bat  to check the display.
echo   To see the task status later:  status.bat
echo.
pause
exit /b 0

:failed
echo.
echo   [x] Could not create the scheduled task.
echo.
echo       Most likely this account is not allowed to create tasks.
echo       Try again like this:
echo         right-click install.bat  ^>  "Run as administrator"
echo.
pause
exit /b 1
