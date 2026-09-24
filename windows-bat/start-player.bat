@echo off
rem ============================================================
rem  Chengyu Cards - start the morning kiosk display
rem  Launched by Windows Task Scheduler, Mon-Fri 07:30.
rem
rem  This file is intentionally ASCII-only so it works no matter
rem  what console code page the machine uses.
rem
rem  It does NOT decide whether today is a school day or whether
rem  the time is right - the web page does that itself. The task
rem  trigger already limits this to Mon-Fri.
rem ============================================================
setlocal

set "URL=https://simon05091004.github.io/chengyu-cards/"
set "PROFILE=%LOCALAPPDATA%\ChengyuKiosk"

set "BROWSER="
set "IMAGE="

rem --- prefer Microsoft Edge (built into Windows) ---
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if defined BROWSER set "IMAGE=msedge.exe"

rem --- fall back to Google Chrome ---
if not defined BROWSER if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined IMAGE if defined BROWSER set "IMAGE=chrome.exe"

if not defined BROWSER exit /b 2

rem --- remember which browser we used, so stop-player.bat closes the right one ---
if not exist "%PROFILE%" mkdir "%PROFILE%" >nul 2>&1
> "%PROFILE%\browser.txt" echo %IMAGE%

start "" "%BROWSER%" --kiosk "%URL%" --edge-kiosk-type=fullscreen --no-first-run --noerrdialogs --disable-infobars --disable-session-crashed-bubble --user-data-dir="%PROFILE%"

exit /b 0
