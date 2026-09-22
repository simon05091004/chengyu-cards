# 成語卡自動播放 - 移除排程
# 如果不想再自動播放了，用系統管理員身分執行這個腳本即可清乾淨（用法同「安裝排程.ps1」）。

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "請用『系統管理員』身分執行這個腳本（作法同安裝排程.ps1）。" -ForegroundColor Yellow
    exit 1
}

Unregister-ScheduledTask -TaskName "成語卡_開始播放" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "成語卡_停止播放" -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "已移除「成語卡_開始播放」「成語卡_停止播放」兩個排程工作。" -ForegroundColor Green
Write-Host "如果現在正好在播放中，畫面不會馬上消失，可以手動按 Alt+F4 關閉瀏覽器視窗。"
