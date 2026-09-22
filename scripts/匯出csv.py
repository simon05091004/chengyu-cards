# -*- coding: utf-8 -*-
"""把成語資料庫匯出成 Canva Bulk Create 用的 CSV。

用法: python3 scripts/匯出csv.py
輸出: output/canva批量資料.csv（UTF-8 with BOM，Excel 與 Canva 都能正常開）
"""
import json, csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "成語資料.json")
OUT  = os.path.join(ROOT, "output", "canva批量資料.csv")

COLS = ["課次標籤", "成語", "注音", "注音1", "注音2", "注音3", "注音4", "拼音", "解釋", "白話解釋",
        "例句1", "例句2", "例句3", "出處", "近義詞", "反義詞", "易錯提醒"]

def row(i):
    ex = i.get("例句", []) + ["", "", ""]
    return {
        "課次標籤": f"國語　{i['課次']}　成語 {i['序號']}",
        "成語": i["成語"],
        "注音": i["注音"],
        **{f"注音{n}": (i["注音"].split() + ["", "", "", ""])[n-1] for n in range(1, 5)},
        "拼音": i.get("拼音", ""),
        "解釋": i["解釋"],
        "白話解釋": i.get("白話解釋", ""),
        "例句1": ex[0], "例句2": ex[1], "例句3": ex[2],
        "出處": i.get("出處", ""),
        "近義詞": "、".join(i.get("近義詞", [])),
        "反義詞": "、".join(i.get("反義詞", [])),
        "易錯提醒": i.get("易錯提醒", ""),
    }

def main():
    db = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for i in db["成語"]:
            w.writerow(row(i))
    print(f"已匯出 {len(db['成語'])} 筆 → {OUT}")
    print("欄位：" + "、".join(COLS))

if __name__ == "__main__":
    main()
