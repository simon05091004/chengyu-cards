# -*- coding: utf-8 -*-
"""成語教學圖卡產生器

  文字版  1600×1200   python3 scripts/產圖.py
  插圖版  1600×1600   python3 scripts/產圖.py --插圖
                      （會自動抓 output/插圖/{編號}_{成語}.png）
"""
import json, os, argparse
from PIL import Image, ImageDraw, ImageFont
import 標籤 as 標籤模組

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA   = os.path.join(ROOT, "data", "成語資料.json")
OUT    = os.path.join(ROOT, "output")
ILLDIR = os.path.join(OUT, "插圖")

F_BOLD  = "/System/Library/Fonts/STHeiti Medium.ttc"
F_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"

BG     = "#FAF6EE"
INK    = "#2B2B2B"
RED    = "#8C2F26"
GOLD   = "#C9A227"
GRAY   = "#6E6459"
WARNBG = "#FBEFE4"
WARNFG = "#B4501F"

W      = 1600
H_TEXT = 1200      # 文字版高度
H_ILL  = 1600      # 插圖版高度
ILL_H  = 560       # 插圖橫幅高度
M      = 96        # 左右邊界

def font(p, s):
    return ImageFont.truetype(p, s)

def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def draw_block(draw, x, y, text, fnt, fill, max_w, gap=18):
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + gap
    return y

def paste_banner(img, path, inset=28):
    """插圖等比填滿框內橫幅，置中裁切，底部漸層淡出到底色"""
    bw = W - inset * 2
    ill = Image.open(path).convert("RGB")
    s = max(bw / ill.width, ILL_H / ill.height)
    ill = ill.resize((round(ill.width * s), round(ill.height * s)), Image.LANCZOS)
    left = (ill.width - bw) // 2
    top  = (ill.height - ILL_H) // 3        # 偏上裁切，保留主體
    ill = ill.crop((left, top, left + bw, top + ILL_H))

    mask = Image.new("L", (bw, ILL_H), 255)
    md = ImageDraw.Draw(mask)
    fade = 190
    for i in range(fade):
        md.line([(0, ILL_H - fade + i), (bw, ILL_H - fade + i)],
                fill=int(255 * (1 - i / fade) ** 1.4))
    img.paste(ill, (inset, inset), mask)

def make_card(item, out_path, illustration=None):
    H = H_ILL if illustration else H_TEXT
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    CW = W - M * 2

    if illustration:
        paste_banner(img, illustration)

    # 外框
    d.rectangle([26, 26, W - 27, H - 27], outline="#DCD2C0", width=3)
    d.rectangle([38, 38, W - 39, H - 39], outline="#E9E2D4", width=1)

    # 課次標籤
    f_tag = font(F_BOLD, 32)
    tag = item["標籤"]
    d.rectangle([M, 74, M + d.textlength(tag, font=f_tag) + 44, 128], fill=RED)
    d.text((M + 22, 83), tag, font=f_tag, fill="#FFF8F0")

    # 成語大字 + 逐字注音
    word, zhuyin = item["成語"], item["注音"].split()
    f_word, f_zy = font(F_BOLD, 156), font(F_LIGHT, 34)
    cell = 210
    x0 = (W - cell * len(word)) // 2
    y_zy   = (ILL_H + 54) if illustration else 186
    y_word = y_zy + 50

    for i, ch in enumerate(word):
        cx = x0 + i * cell + cell // 2
        if i < len(zhuyin):
            d.text((cx - d.textlength(zhuyin[i], font=f_zy) / 2, y_zy),
                   zhuyin[i], font=f_zy, fill=GRAY)
        d.text((cx - d.textlength(ch, font=f_word) / 2, y_word), ch, font=f_word, fill=INK)

    f_py = font(F_LIGHT, 30)
    py = item.get("拼音", "")
    d.text(((W - d.textlength(py, font=f_py)) / 2, y_word + 178), py, font=f_py, fill=GOLD)

    y = y_word + 232
    d.line([M, y, W - M, y], fill="#DCD2C0", width=2)
    y += 40

    f_h, f_b = font(F_BOLD, 38), font(F_LIGHT, 34)

    def heading(y, label):
        d.rectangle([M, y + 6, M + 8, y + 40], fill=GOLD)
        d.text((M + 24, y), label, font=f_h, fill=RED)
        return y + 60

    y = heading(y, "解釋")
    y = draw_block(d, M + 24, y, item["解釋"], f_b, INK, CW - 24, gap=16) + 6
    y = draw_block(d, M + 24, y, "（白話）" + item["白話解釋"],
                   font(F_LIGHT, 30), GRAY, CW - 24, gap=14) + 26

    y = heading(y, "例句")
    f_num = font(F_BOLD, 30)
    for i, s in enumerate(item["例句"], 1):
        d.ellipse([M + 24, y + 4, M + 58, y + 38], fill=RED)
        n = str(i)
        d.text((M + 41 - d.textlength(n, font=f_num) / 2, y + 7), n, font=f_num, fill="#FFF8F0")
        y = draw_block(d, M + 78, y, s, f_b, INK, CW - 78, gap=12) + 14

    warn = item.get("易錯提醒")
    if warn:
        f_w = font(F_LIGHT, 28)
        lines = wrap(d, warn, f_w, CW - 130)
        box_h = len(lines) * (f_w.size + 12) + 46
        by = H - 74 - box_h
        d.rounded_rectangle([M, by, W - M, by + box_h], radius=14,
                            fill=WARNBG, outline="#E8C9AE", width=2)
        d.text((M + 26, by + 20), "※", font=font(F_BOLD, 30), fill=WARNFG)
        ty = by + 22
        for line in lines:
            d.text((M + 70, ty), line, font=f_w, fill=WARNFG)
            ty += f_w.size + 12

    img.save(out_path, "PNG")
    return out_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--編號", default=None)
    ap.add_argument("--插圖", action="store_true", help="套用 output/插圖/ 的插畫，輸出插圖版")
    ap.add_argument("--投影版", action="store_true", help="輸出 1920×1080 橫式（投影用）")
    a = ap.parse_args()

    if a.投影版:
        globals()["W"], globals()["H_TEXT"] = 1920, 1080
    db = 標籤模組.標註(json.load(open(DATA, encoding="utf-8")))
    os.makedirs(OUT, exist_ok=True)
    for item in db["成語"]:
        if a.編號 and item["編號"] != a.編號:
            continue
        stem = f"{item['編號']}_{item['成語']}"
        ill = None
        if a.插圖:
            ill = os.path.join(ILLDIR, stem + ".png")
            if not os.path.exists(ill):
                print(f"略過 {stem}：找不到插圖 {ill}")
                continue
        suffix = "_插圖版" if ill else ("_投影版" if a.投影版 else "")
        p = os.path.join(OUT, stem + suffix + ".png")
        make_card(item, p, ill)
        print("已產出:", p)

if __name__ == "__main__":
    main()
