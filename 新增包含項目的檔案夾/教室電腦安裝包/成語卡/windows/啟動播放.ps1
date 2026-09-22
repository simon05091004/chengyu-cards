# 成語卡自動播放 - 啟動器
#
# 由 Windows 工作排程器每天 07:30 觸發（如果電腦那時是關機/睡眠，會在開機後
# 盡快補觸發一次，見「安裝排程.ps1」的 -StartWhenAvailable 設定）。
#
# 這支腳本自己也會再檢查一次現在是不是「上課日」+「在播放時段內」，
# 只要有一項不符合就什麼都不做、直接結束——這樣不管電腦是本來就開著、
# 剛開機、還是在假日被誰打開，都不會在錯的時間跳出全螢幕畫面。

$ErrorActionPreference = "SilentlyContinue"

$root       = Split-Path -Parent $PSScriptRoot
$dataFile   = Join-Path $root "data\播放設定.json"
$htmlFile   = Join-Path $root "output\播放\index.html"
$profileDir = Join-Path $env:LOCALAPPDATA "成語卡Kiosk"

function Get-Config {
    if (Test-Path $dataFile) {
        try { return (Get-Content -Raw -Encoding UTF8 $dataFile) | ConvertFrom-Json } catch { return $null }
    }
    return $null
}

function Convert-ToMinutes([string]$hm) {
    $parts = $hm -split ':'
    return ([int]$parts[0]) * 60 + [int]$parts[1]
}

function Test-Playable($cfg) {
    $now = Get-Date

    if ($now.DayOfWeek -eq 'Saturday' -or $now.DayOfWeek -eq 'Sunday') {
        return $false
    }

    $today = $now.ToString("yyyy-MM-dd")

    if ($cfg -and $cfg.'學期起訖') {
        $s = $cfg.'學期起訖'.'開始'
        $e = $cfg.'學期起訖'.'結束'
        if ($s -and ($today -lt $s)) { return $false }
        if ($e -and ($today -gt $e)) { return $false }
    }

    if ($cfg -and $cfg.'停課日') {
        foreach ($d in $cfg.'停課日') {
            if ($d.'日期' -eq $today) { return $false }
        }
    }

    $startStr = "07:30"; $endStr = "08:30"
    if ($cfg -and $cfg.'播放時段') {
        if ($cfg.'播放時段'.'開始') { $startStr = $cfg.'播放時段'.'開始' }
        if ($cfg.'播放時段'.'結束') { $endStr = $cfg.'播放時段'.'結束' }
    }

    $nowMin   = $now.Hour * 60 + $now.Minute
    $startMin = Convert-ToMinutes $startStr
    $endMin   = Convert-ToMinutes $endStr

    return ($nowMin -ge $startMin -and $nowMin -lt $endMin)
}

if (-not (Test-Path $htmlFile)) { exit 1 }

$cfg = Get-Config
if (-not (Test-Playable $cfg)) { exit 0 }

# 已經有一個成語卡專用視窗開著的話就不要再開第二個
$already = Get-CimInstance Win32_Process -Filter "Name='msedge.exe' or Name='chrome.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($profileDir) }
if ($already) { exit 0 }

$candidates = @(
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
$browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { exit 2 }

$url = "file:///" + ($htmlFile -replace '\\', '/')

$argStr = '--kiosk "' + $url + '" --edge-kiosk-type=fullscreen --no-first-run ' +
          '--noerrdialogs --disable-infobars --disable-session-crashed-bubble ' +
          '--user-data-dir="' + $profileDir + '"'

Start-Process -FilePath $browser -ArgumentList $argStr
