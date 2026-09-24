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

rem --- try to enable "wake the computer to run this task" ---
rem schtasks.exe cannot set that option, so we ask PowerShell to do it.
rem An inline -Command is NOT blocked by the PowerShell execution policy
rem (that policy only blocks .ps1 script FILES), so this usually works
rem even on a locked-down school PC. If it fails, we say so below.
set "WAKE=no"
powershell -NoProfile -Command "foreach($n in 'ChengyuCard_Start','ChengyuCard_Stop'){ $t=Get-ScheduledTask -TaskName $n -ErrorAction Stop; $t.Settings.WakeToRun=$true; Set-ScheduledTask -InputObject $t -ErrorAction Stop | Out-Null }" >nul 2>&1
if not errorlevel 1 set "WAKE=yes"

echo.
echo   [OK] Installed. Two tasks now exist:
echo.
echo        ChengyuCard_Start    Mon-Fri  07:30
echo        ChengyuCard_Stop     Mon-Fri  08:30
echo.
if "%WAKE%"=="yes" (
  echo   [OK] "Wake the computer to run this task" is enabled.
) else (
  echo   [!] Could not enable "wake the computer to run this task".
  echo       If the PC is asleep at 07:30 it will NOT wake up by itself.
  echo       Fix it by hand, it is one checkbox:
  echo         Task Scheduler ^> Task Scheduler Library ^> ChengyuCard_Start
  echo         right-click ^> Properties ^> Conditions tab
  echo         tick "Wake the computer to run this task" ^> OK
)
echo.
echo   Strongly recommended for a classroom display:
echo     run  setup-power.bat  as Administrator, so the PC never
echo     sleeps at all. That is far more reliable than waking it.
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
