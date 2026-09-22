# 成語卡自動播放 - 停止腳本
#
# 由 Windows 工作排程器每天 08:30 觸發。只會關掉「用成語卡專用設定檔」
# 開起來的那個瀏覽器視窗（用 --user-data-dir 的路徑當標記），
# 不會動到老師自己另外開的 Edge/Chrome 視窗或分頁。

$ErrorActionPreference = "SilentlyContinue"
$profileDir = Join-Path $env:LOCALAPPDATA "成語卡Kiosk"

Get-CimInstance Win32_Process -Filter "Name='msedge.exe' or Name='chrome.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($profileDir) } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force } catch {}
    }
