# 成語卡自動播放 - 立即預覽
#
# 用一般視窗（不是全螢幕 kiosk）打開播放頁，網址加 ?demo=1 讓它無視時間判斷、
# 直接開始輪播，方便隨時檢查畫面內容對不對，不用等到隔天 07:30。
# 雙擊這個檔案、或右鍵「使用 PowerShell 執行」即可。

$root = Split-Path -Parent $PSScriptRoot
$html = Join-Path $root "output\播放\index.html"

if (-not (Test-Path $html)) {
    Write-Host "找不到 $html" -ForegroundColor Red
    Write-Host "請先在原本那台電腦上執行「python3 scripts/產出播放頁.py」產生播放頁，再把整個資料夾複製過來這台電腦。" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
    exit 1
}

$url = "file:///" + ($html -replace '\\', '/') + "?demo=1"
Start-Process $url
