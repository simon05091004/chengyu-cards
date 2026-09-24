@echo off
rem ============================================================
rem  Chengyu Cards - close the morning kiosk display
rem  Launched by Windows Task Scheduler, Mon-Fri 08:30.
rem
rem  NOTE: this closes ALL windows of the browser that was used
rem  for the kiosk (normally Microsoft Edge). Pure batch cannot
rem  target one single window reliably.
rem
rem  Practical rule for the classroom PC:
rem    - let the kiosk use Edge  (it does, by default)
rem    - use Chrome for your own teaching material
rem  Then nothing of yours is ever closed at 08:30.
rem ============================================================
setlocal

set "PROFILE=%LOCALAPPDATA%\ChengyuKiosk"
set "IMAGE="

if exist "%PROFILE%\browser.txt" set /p IMAGE=<"%PROFILE%\browser.txt"
if not defined IMAGE set "IMAGE=msedge.exe"

taskkill /F /IM %IMAGE% /T >nul 2>&1

exit /b 0
