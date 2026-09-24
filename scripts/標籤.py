# -*- coding: utf-8 -*-
"""成語卡標籤文字的唯一來源。

圖卡、PPTX、Canva CSV、自動播放頁四個輸出都用這一份，改格式只要改這裡。

標籤長這樣：高年級成語（一）、高年級成語（二）…
編號依成語在 data/成語資料.json 的「成語」陣列裡的順序往後排，加新的一筆
就自動接續下去。系列名稱放在該檔的頂層欄位「系列名稱」，要改名字改那裡。
"""

數字 = "零一二三四五六七八九"


def 中文數字(n):
    """1→一、10→十、11→十一、25→二十五、100→一百、105→一百零五、110→一百一十"""
    if n < 0:
        return str(n)
    if n < 10:
        return 數字[n]
    if n < 20:
        return "十" + (數字[n % 10] if n % 10 else "")
    if n < 100:
        return 數字[n // 10] + "十" + (數字[n % 10] if n % 10 else "")
    if n < 1000:
        s = 數字[n // 100] + "百"
        r = n % 100
        if r == 0:
            return s
        if r < 10:
            return s + "零" + 數字[r]
        if r < 20:
            return s + "一十" + (數字[r % 10] if r % 10 else "")
        return s + 數字[r // 10] + "十" + (數字[r % 10] if r % 10 else "")
    return str(n)


def 系列名稱(db):
    return db.get("系列名稱") or "高年級成語"


def 單筆標籤(db, 索引):
    """索引為 0 起算的陣列位置"""
    return f"{系列名稱(db)}（{中文數字(索引 + 1)}）"


def 標註(db):
    """把每一筆的顯示標籤算好塞進 item['標籤']。

    只影響這次執行時記憶體裡的資料，不會寫回 data/成語資料.json。
    """
    for i, item in enumerate(db.get("成語", [])):
        item["標籤"] = 單筆標籤(db, i)
    return db
