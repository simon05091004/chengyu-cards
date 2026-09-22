# -*- coding: utf-8 -*-
"""更新成語資料庫後，一次重新產生所有輸出。

用法: python3 scripts/全部更新.py
會依序執行:
  1. 匯出csv.py     → output/canva批量資料.csv（給 Canva Bulk Create 用）
  2. 產出播放頁.py   → output/播放/index.html（給教室電腦早自習自動播放用）
"""
import subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = ["匯出csv.py", "產出播放頁.py"]

def main():
    for name in STEPS:
        path = os.path.join(ROOT, "scripts", name)
        print(f"── 執行 {name} ──", flush=True)
        result = subprocess.run([sys.executable, path])
        if result.returncode != 0:
            print(f"✗ {name} 執行失敗（結束碼 {result.returncode}），後面的步驟已中止。")
            sys.exit(result.returncode)
        print()
    print("全部更新完成。")
    print("Canva：把 output/canva批量資料.csv 重新上傳到模板的大量建立即可。")
    print("自動播放：把更新後的 data/ 與 output/播放/ 複製到教室電腦上覆蓋舊檔即可（見 windows/README_安裝步驟.md）。")

if __name__ == "__main__":
    main()
