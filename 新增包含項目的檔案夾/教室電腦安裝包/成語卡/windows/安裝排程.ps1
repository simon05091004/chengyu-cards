# 成語卡自動播放 - 安裝排程（只需要在教室這台電腦上執行「一次」）
#
# 用法：
#   1. 開始功能表找「Windows PowerShell」，右鍵 →「以系統管理員身分執行」
#   2. 在跳出的視窗裡輸入 cd，後面接這個 windows 資料夾的路徑，按 Enter
#      例如: cd "C:\成語卡\windows"
#   3. 輸入以下指令並 Enter：
#      powershell -ExecutionPolicy Bypass -File .\安裝排程.ps1

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "請用『系統管理員』身分執行這個腳本：" -ForegroundColor Yellow
    Write-Host "開始功能表找 Windows PowerShell → 右鍵 →「以系統管理員身分執行」，再重新執行本檔一次。" -ForegroundColor Yellow
    exit 1
}

$startScript = Join-Path $PSScriptRoot "啟動播放.ps1"
$stopScript  = Join-Path $PSScriptRoot "停止播放.ps1"

if (-not (Test-Path $startScript) -or -not (Test-Path $stopScript)) {
    Write-Host "找不到 啟動播放.ps1 / 停止播放.ps1，請確認整個 windows 資料夾都有複製過來。" -ForegroundColor Red
    exit 1
}

# 確認播放頁與設定檔也都在（只複製 windows 資料夾是不夠的）
$root     = Split-Path -Parent $PSScriptRoot
$htmlFile = Join-Path $root "output\播放\index.html"
$dataFile = Join-Path $root "data\播放設定.json"

if (-not (Test-Path $htmlFile)) {
    Write-Host "找不到播放頁：$htmlFile" -ForegroundColor Red
    Write-Host "請把整個資料夾（含 data 與 output\播放）都複製過來，不能只複製 windows 資料夾。" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $dataFile)) {
    Write-Host "找不到設定檔：$dataFile" -ForegroundColor Red
    Write-Host "請把整個資料夾（含 data 與 output\播放）都複製過來，不能只複製 windows 資料夾。" -ForegroundColor Red
    exit 1
}

# 排程時間直接取自 data\播放設定.json，跟播放頁用同一份設定，不會對不上
$startHM = "07:30"; $endHM = "08:30"
try {
    $cfg = (Get-Content -Raw -Encoding UTF8 $dataFile) | ConvertFrom-Json
    if ($cfg.'播放時段'.'開始') { $startHM = $cfg.'播放時段'.'開始' }
    if ($cfg.'播放時段'.'結束') { $endHM   = $cfg.'播放時段'.'結束' }
} catch {
    Write-Host "播放設定.json 讀取失敗，排程時間改用預設的 07:30 / 08:30。" -ForegroundColor Yellow
}

function ConvertTo-TriggerTime([string]$hm) {
    $parts = $hm -split ':'
    return (Get-Date -Hour ([int]$parts[0]) -Minute ([int]$parts[1]) -Second 0 -Millisecond 0)
}
$startTime = ConvertTo-TriggerTime $startHM
$endTime   = ConvertTo-TriggerTime $endHM

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$actionStart = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""
$triggerStart = New-ScheduledTaskTrigger -Daily -At $startTime

$actionStop = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$stopScript`""
$triggerStop = New-ScheduledTaskTrigger -Daily -At $endTime

Register-ScheduledTask -TaskName "成語卡_開始播放" -Action $actionStart -Trigger $triggerStart `
    -Settings $settings -Description "早自習成語卡自動播放：$startHM 觸發，腳本會自行判斷上課日與播放時段" -Force | Out-Null

Register-ScheduledTask -TaskName "成語卡_停止播放" -Action $actionStop -Trigger $triggerStop `
    -Settings $settings -Description "早自習成語卡自動關閉：$endHM 觸發" -Force | Out-Null

Write-Host "安裝完成！已建立兩個排程工作（在「工作排程器」的『工作排程器程式庫』可以查到）：" -ForegroundColor Green
Write-Host "  - 成語卡_開始播放（每天 $startHM）"
Write-Host "  - 成語卡_停止播放（每天 $endHM）"
Write-Host ""
Write-Host "這兩個排程只有「現在登入的這個 Windows 帳號」每天有登入時才會觸發。" -ForegroundColor Cyan
Write-Host "如果教室電腦是共用帳號、平常都開著或每天會登入，這樣就沒問題；" -ForegroundColor Cyan
Write-Host "如果常常整台關機、且登入的人不固定，請告知需要改成「不論使用者是否登入都執行」，" -ForegroundColor Cyan
Write-Host "那個模式需要輸入一次 Windows 密碼讓工作排程器記住，要另外用工作排程器介面設定。" -ForegroundColor Cyan
Write-Host ""
Write-Host "現在就想看效果、不想等明天 $startHM → 執行同資料夾裡的「立即測試.ps1」（一般視窗預覽，不會鎖全螢幕）。"
