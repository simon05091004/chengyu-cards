# -*- coding: utf-8 -*-
"""打包一份可以直接帶去教室電腦的安裝包。

用法: python3 scripts/打包教室電腦.py
輸出: output/教室電腦安裝包/成語卡/   ← 直接拖到隨身碟用這個
      output/教室電腦安裝包.zip       ← 走雲端硬碟/email 傳輸用這個

包裡只有教室那台 Windows 電腦真正需要的檔案：
    成語卡/data/播放設定.json      （啟動腳本判斷上課日/播放時段用）
    成語卡/output/播放/index.html  （播放頁本身，成語內容都包在裡面）
    成語卡/windows/*.ps1           （排程腳本）
    成語卡/windows/README_安裝步驟.md

刻意「不」放進去的東西：
    金鑰.txt        Gemini API 金鑰，不應該出現在學校共用電腦上
    scripts/        教室電腦不需要 Python，也不會在那邊產圖
    output 的圖檔   教室電腦用不到，只會讓包變大

解壓縮後把裡面的「成語卡」資料夾整個放到 C:\\ 即可（C:\\成語卡\\...）。
"""
import os, sys, shutil, subprocess, zipfile

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ZIP = os.path.join(ROOT, "output", "教室電腦安裝包.zip")
OUT_DIR = os.path.join(ROOT, "output", "教室電腦安裝包")
TOP     = "成語卡"

# (專案裡的相對路徑, 壓縮檔裡的相對路徑)
FILES = [
    ("data/播放設定.json",             f"{TOP}/data/播放設定.json"),
    ("output/播放/index.html",         f"{TOP}/output/播放/index.html"),
    ("windows/啟動播放.ps1",           f"{TOP}/windows/啟動播放.ps1"),
    ("windows/停止播放.ps1",           f"{TOP}/windows/停止播放.ps1"),
    ("windows/安裝排程.ps1",           f"{TOP}/windows/安裝排程.ps1"),
    ("windows/移除排程.ps1",           f"{TOP}/windows/移除排程.ps1"),
    ("windows/立即測試.ps1",           f"{TOP}/windows/立即測試.ps1"),
    ("windows/README_安裝步驟.md",     f"{TOP}/windows/README_安裝步驟.md"),
]


def main():
    # 先重新產生播放頁，確保包裡是最新內容
    print("── 先重新產生播放頁 ──", flush=True)
    result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "產出播放頁.py")])
    if result.returncode != 0:
        print("✗ 產出播放頁.py 失敗，已中止打包。")
        sys.exit(result.returncode)
    print()

    missing = [src for src, _ in FILES if not os.path.exists(os.path.join(ROOT, src))]
    if missing:
        print("✗ 找不到這些檔案，無法打包：")
        for m in missing:
            print("   ", m)
        sys.exit(1)

    # 1) 資料夾版：直接拖到隨身碟，不經過 zip 的檔名編碼，最保險
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    for src, dst in FILES:
        target = os.path.join(OUT_DIR, dst)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, src), target)

    # 2) zip 版：走雲端硬碟或 email 時用（Python 會設 UTF-8 檔名旗標，Win10/11 解得開）
    os.makedirs(os.path.dirname(OUT_ZIP), exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for src, dst in FILES:
            z.write(os.path.join(ROOT, src), dst)

    size_kb = os.path.getsize(OUT_ZIP) / 1024
    print(f"已打包 {len(FILES)} 個檔案：")
    print(f"  資料夾版 → {os.path.join(OUT_DIR, TOP)}（拖到隨身碟用這個）")
    print(f"  ZIP  版 → {OUT_ZIP}（{size_kb:.0f} KB，走雲端硬碟用這個）")
    print(f"到教室電腦後把「{TOP}」資料夾整個放到 C:\\ ，再依 windows/README_安裝步驟.md 執行安裝排程.ps1。")
    print("（金鑰.txt 與 scripts/ 沒有放進去，不會被帶到學校電腦上。）")


if __name__ == "__main__":
    main()
