# -*- coding: utf-8 -*-
"""呼叫 Gemini 影像模型產生成語情境插畫，並接著產出插圖版圖卡。

金鑰讀取順序：環境變數 GEMINI_API_KEY → 專案根目錄的 .env

用法:
    python3 scripts/gemini_插圖.py --列出模型          # 確認金鑰可用的模型
    python3 scripts/gemini_插圖.py --編號 L01-01       # 產插畫 + 圖卡
    python3 scripts/gemini_插圖.py --只印指令          # 不呼叫 API，只看 prompt
"""
import json, os, sys, base64, argparse, subprocess, urllib.request, urllib.error

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(ROOT, "data", "成語資料.json")
OUT   = os.path.join(ROOT, "output", "插圖")
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
BASE  = "https://generativelanguage.googleapis.com/v1beta"

def load_key():
    """金鑰讀取順序：環境變數 → 金鑰.txt → .env"""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    for name in ("金鑰.txt", ".env"):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "GEMINI_API_KEY":
                    v = v.strip().strip('"').strip("'")
                    if v:
                        return v
            else:                      # 整行就是金鑰本身
                return line
    sys.exit("找不到金鑰。請把金鑰貼進專案裡的「金鑰.txt」存檔\n"
             "（免費申請：https://aistudio.google.com/apikey）")

def api(path, key, payload=None, timeout=300):
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(payload).encode() if payload else None,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 429 and "limit: 0" in body:
            sys.exit(
                "\n免費層沒有開放產圖模型（額度為 0），這是 Google 的方案限制，不是設定錯誤。\n"
                "兩個解法：\n"
                "  A. 到 https://aistudio.google.com/apikey 對你的專案點「Set up billing」開通付費\n"
                "  B. 改用 AI Studio 網頁版免費產圖：\n"
                "     1) python3 scripts/gemini_插圖.py --編號 XXX --只印指令   ← 取得產圖指令\n"
                "     2) 貼到 https://aistudio.google.com 產圖後下載\n"
                "     3) 存成 output/插圖/{編號}_{成語}.png\n"
                "     4) python3 scripts/產圖.py --編號 XXX --插圖              ← 套版\n")
        if e.code == 429:
            sys.exit(f"\n額度用盡或請求過快（429）。稍後再試。\n{body[:400]}")
        sys.exit(f"Gemini API 錯誤 {e.code}：{body[:600]}")
    except urllib.error.URLError as e:
        sys.exit(f"連線失敗：{e.reason}")

def build_prompt(item):
    """把 成語-解釋-例句 三項組成給 Gemini 的產圖指令"""
    return (
        "請畫一張適合國小學生的成語情境插畫，橫式構圖，主體置中偏上，畫面乾淨、留白充足。\n"
        "風格：溫潤的中國風水彩，米白宣紙底色，赭紅與墨綠為主調，線條柔和，不要濃重陰影。\n"
        "重要：畫面中絕對不要出現任何文字、字母或數字。\n\n"
        f"成語：{item['成語']}\n"
        f"解釋：{item['解釋']}\n"
        f"例句情境：{item['例句'][0]}\n\n"
        "請依上述例句的情境作畫，讓學生一看就能聯想到這個成語的意思。"
    )

def generate(item, key):
    res = api(f"models/{MODEL}:generateContent", key, {
        "contents": [{"parts": [{"text": build_prompt(item)}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    })
    for part in res.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            os.makedirs(OUT, exist_ok=True)
            p = os.path.join(OUT, f"{item['編號']}_{item['成語']}.png")
            with open(p, "wb") as f:
                f.write(base64.b64decode(part["inlineData"]["data"]))
            return p
    sys.exit("回應中沒有影像資料：" + json.dumps(res, ensure_ascii=False)[:600])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--編號", default=None)
    ap.add_argument("--只印指令", action="store_true")
    ap.add_argument("--列出模型", action="store_true")
    a = ap.parse_args()

    if a.列出模型:
        for m in api("models", load_key())["models"]:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(m["name"].replace("models/", ""))
        return

    db = json.load(open(DATA, encoding="utf-8"))
    items = [i for i in db["成語"] if not a.編號 or i["編號"] == a.編號]
    if not items:
        sys.exit("找不到指定編號")

    if a.只印指令:
        d = os.path.join(ROOT, "output", "產圖指令")
        os.makedirs(d, exist_ok=True)
        for i in items:
            t = build_prompt(i)
            f = os.path.join(d, f"{i['編號']}_{i['成語']}.txt")
            open(f, "w", encoding="utf-8").write(t)
            print("=" * 60); print(t); print(f"\n（已存成 {f}）")
        return

    key = load_key()
    for i in items:
        print(f"[{i['成語']}] 產生插畫中…（模型 {MODEL}）")
        print("  插畫:", generate(i, key))
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "產圖.py"),
                        "--編號", i["編號"], "--插圖"], check=True)

if __name__ == "__main__":
    main()
