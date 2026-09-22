# 成語卡自動播放 - 立即預覽
#
# 用一般視窗（不是全螢幕 kiosk）打開播放頁，網址加 ?demo=1 讓它無視時間判斷、
# 直接開始輪播，方便隨時檢查內容對不對，不用等到隔天 07:30。
# 雙擊這個檔案、或右鍵「使用 PowerShell 執行」即可。

$ErrorActionPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$siteUrl = "https://simon05091004.github.io/chengyu-cards/"

$root      = Split-Path -Parent $PSScriptRoot
$localHtml = Join-Path $root "output\播放\index.html"

# 線上版連得到就用線上版（跟每天早上實際播的是同一份）
$reachable = $false
try {
    $r = Invoke-WebRequest -Uri $siteUrl -TimeoutSec 8 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $reachable = $true }
} catch { }

if ($reachable) {
    Start-Process ($siteUrl + "?demo=1")
    Write-Host "已用線上版開啟（$siteUrl）。這就是每天早上會播的那一份。" -ForegroundColor Green
}
elseif (Test-Path $localHtml) {
    $url = "file:///" + ($localHtml -replace '\\', '/') + "?demo=1"
    Start-Process $url
    Write-Host "連不到線上版，改用本機備份檔開啟。" -ForegroundColor Yellow
    Write-Host "如果這台電腦早上也連不到網路，請確認學校網路，或告知需要改回純本機模式。" -ForegroundColor Yellow
}
else {
    Write-Host "線上版連不到，本機也找不到 $localHtml" -ForegroundColor Red
    Write-Host "請確認這台電腦有網路，或重新複製一份安裝包過來。" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
}
