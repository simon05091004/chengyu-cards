@echo off
rem ============================================================
rem  Chengyu Cards - power settings for a classroom display PC
rem
rem  Run this ONCE, as Administrator.
rem
rem  What it does (only while plugged in to AC power):
rem    - never put the computer to sleep
rem    - never turn the display off
rem    - allow wake timers, so a scheduled task CAN wake the PC
rem
rem  Not touched on purpose: the "require sign-in on wakeup"
rem  setting. That is a security setting on a shared school PC,
rem  so it is left for you / your IT staff to decide.
rem ============================================================
setlocal

net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo   [x] Please run this as Administrator.
  echo       Right-click setup-power.bat  ^>  "Run as administrator"
  echo.
  pause
  exit /b 1
)

echo.
echo  ============================================
echo   Chengyu Cards - classroom power settings
echo  ============================================
echo.

echo  - never sleep (on AC)
powercfg /change standby-timeout-ac 0
echo  - never hibernate (on AC)
powercfg /change hibernate-timeout-ac 0
echo  - never turn the display off (on AC)
powercfg /change monitor-timeout-ac 0
echo  - allow wake timers
powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /setactive SCHEME_CURRENT

echo.
echo   [OK] Done.
echo.
echo   The PC will now stay awake while plugged in, which is the
echo   most reliable setup for a display that must show something
echo   at 07:30 every school day.
echo.
pause
