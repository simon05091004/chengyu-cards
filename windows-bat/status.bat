@echo off
rem ============================================================
rem  Chengyu Cards - show whether the tasks exist, when they
rem  last ran and when they will run next.
rem
rem  No text filtering here on purpose: schtasks prints its
rem  field names in the Windows display language, so filtering
rem  on English words would wrongly report "not found" on a
rem  Chinese version of Windows.
rem ============================================================
echo.
echo  ============ ChengyuCard_Start ============
schtasks /Query /TN "ChengyuCard_Start" >nul 2>&1
if errorlevel 1 (
  echo   [x] Task not found. Run install.bat first.
) else (
  schtasks /Query /TN "ChengyuCard_Start" /FO LIST /V
)

echo.
echo  ============ ChengyuCard_Stop =============
schtasks /Query /TN "ChengyuCard_Stop" >nul 2>&1
if errorlevel 1 (
  echo   [x] Task not found. Run install.bat first.
) else (
  schtasks /Query /TN "ChengyuCard_Stop" /FO LIST /V
)

echo.
pause
