# -*- coding: utf-8 -*-
"""產生「早自習成語卡自動播放」用的單一 HTML 檔。

用法: python3 scripts/產出播放頁.py
輸出: output/播放/index.html

這個 HTML 是完全離線、自己會判斷時間的播放頁：
  - 成語資料庫、播放設定（學期範圍・停課日・播放時段）都在產生的當下
    直接包進 HTML 檔裡，不會在瀏覽器裡另外抓檔案
    （kiosk 模式常用 file:// 開啟，瀏覽器會擋 fetch 本機檔案，所以用「包進去」最穩）。
  - 每次打開，頁面自己看現在時間：
      非上課日（週末／學期外／停課日清單） → 顯示待機畫面
      上課日但還沒到播放時段、或已經超過播放時段 → 顯示待機畫面
      上課日且在播放時段內 → 輪播「今日成語」＋「複習」
  - 「今日成語」= data/成語資料.json 裡最後一筆；也可以在該檔加一個頂層欄位
    "今日編號": "L01-02" 來手動指定。
  - 網址加上 ?demo=1 可以無視時間，強制一直輪播（方便測試、預覽）。

改了 data/成語資料.json 或 data/播放設定.json 之後，要重跑這個腳本，
輸出的 index.html 才會更新（詳見 data/播放設定.json 的備註）。
"""
import json, os

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA      = os.path.join(ROOT, "data", "成語資料.json")
SCHEDULE  = os.path.join(ROOT, "data", "播放設定.json")
OUT_DIR   = os.path.join(ROOT, "output", "播放")
OUT       = os.path.join(OUT_DIR, "index.html")
# GitHub Pages 服務目錄（Settings → Pages 設成 main 分支的 /docs）
DOCS_DIR  = os.path.join(ROOT, "docs")
DOCS_HTML = os.path.join(DOCS_DIR, "index.html")
DOCS_SW   = os.path.join(DOCS_DIR, "sw.js")
DOCS_CFG  = os.path.join(DOCS_DIR, "schedule.json")  # 純 ASCII 檔名，給 PowerShell 抓

# 離線快取：先走網路（確保拿到最新內容），逾時或斷網就用快取。
# 只要成功載入過一次，之後學校網路掛掉照樣能播。
SERVICE_WORKER = r"""const CACHE = "chengyu-cards";
const ASSETS = ["./", "./index.html"];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){ return k !== CACHE; })
                            .map(function(k){ return caches.delete(k); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(e){
  if (e.request.method !== "GET") return;
  e.respondWith(networkFirst(e.request));
});

function withTimeout(p, ms){
  return Promise.race([
    p,
    new Promise(function(_, reject){
      setTimeout(function(){ reject(new Error("timeout")); }, ms);
    })
  ]);
}

async function networkFirst(request){
  const cache = await caches.open(CACHE);
  try {
    const fresh = await withTimeout(fetch(request, { cache: "no-store" }), 4000);
    if (fresh && fresh.ok) { cache.put(request, fresh.clone()); }
    return fresh;
  } catch (err) {
    const cached = (await cache.match(request)) || (await cache.match("./index.html"));
    if (cached) return cached;
    throw err;
  }
}
"""

HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>成語卡自動播放</title>
<style>
  :root{
    --bg:#FAF6EE; --ink:#2B2B2B; --red:#8C2F26; --gold:#C9A227;
    --gray:#6E6459; --warnbg:#FBEFE4; --warnfg:#B4501F;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html{
    font-size: clamp(14px, 1.55vw, 27px);
    background:var(--bg);
  }
  body{
    width:100vw;height:100vh;overflow:hidden;
    background:var(--bg); color:var(--ink);
    font-family:"Microsoft JhengHei","PingFang TC","Noto Sans TC","Heiti TC",sans-serif;
    position:relative;
    cursor:none;
  }
  body::before{
    content:"";position:fixed;inset:1.4rem;
    border:2px solid var(--gold); opacity:.55; pointer-events:none; z-index:5;
  }
  body::after{
    content:"";position:fixed;inset:1.9rem;
    border:1px solid var(--gold); opacity:.35; pointer-events:none; z-index:5;
  }
  .stage{
    position:absolute; inset:0;
    display:flex; flex-direction:column; justify-content:center;
    padding: 7vh 8vw;
    opacity:0; transition:opacity .5s ease;
  }
  .stage.show{ opacity:1; }

  .tag{
    display:inline-block; align-self:flex-start;
    background:var(--red); color:#FBEFE4;
    font-size:1.05rem; letter-spacing:.08em; font-weight:700;
    padding:.5em 1.1em; border-radius:999px;
    margin-bottom:2.2rem;
  }
  .tag-review{ background:var(--gold); color:#3a2e07; }

  .heading{
    font-size:2.4rem; font-weight:700; color:var(--ink);
    margin-bottom:1.6rem;
  }
  .heading-sub{ font-size:1.2rem; color:var(--gray); font-weight:400; margin-left:.6em; }

  /* ---- 標題頁：大成語 + 注音 + 拼音 ---- */
  .title-wrap{ display:flex; flex-direction:column; align-items:center; margin:1vh 0 2vh; }
  .glyphs{ display:flex; gap:2.6rem; }
  .glyph{ display:flex; flex-direction:column; align-items:center; }
  .glyph .zh{ font-size:1.5rem; color:var(--gold); margin-bottom:.5rem; letter-spacing:.05em; }
  .glyph .ch{ font-size:7.4rem; font-weight:700; line-height:1; color:var(--ink); }
  .glyph-fallback{ text-align:center; }
  .glyph-fallback .ch-line{ font-size:6.4rem; font-weight:700; color:var(--ink); }
  .glyph-fallback .zh-line{ font-size:1.6rem; color:var(--gold); margin-top:.8rem; }
  .pinyin{ font-size:1.7rem; color:var(--gold); margin-top:1.6rem; letter-spacing:.06em; }

  /* ---- 字義拆解 ---- */
  .mgrid{ display:flex; flex-wrap:wrap; gap:1.4rem 2.2rem; }
  .mrow{
    display:flex; align-items:baseline; gap:1rem;
    background:#fff; border:1px solid #ECE3D2; border-radius:1rem;
    padding:1rem 1.6rem; flex:1 1 40%;
  }
  .mchar{ font-size:2.3rem; font-weight:700; color:var(--red); }
  .mdesc{ font-size:1.35rem; color:var(--ink); }

  /* ---- 解釋 ---- */
  .block{ margin-bottom:1.8rem; }
  .label{
    font-size:1.15rem; font-weight:700; color:var(--red);
    border-left:.35rem solid var(--red); padding-left:.7rem; margin-bottom:.7rem;
  }
  .text-lg{ font-size:1.75rem; line-height:1.65; }
  .text-md{ font-size:1.4rem; line-height:1.6; color:var(--ink); }
  .muted{ color:var(--gray); }

  /* ---- 例句 ---- */
  .ex-list{ display:flex; flex-direction:column; gap:1.3rem; }
  .ex-row{ display:flex; align-items:flex-start; gap:1.1rem; }
  .ex-num{
    flex:0 0 auto; width:2.1rem; height:2.1rem; border-radius:50%;
    background:var(--red); color:#fff; font-size:1.15rem; font-weight:700;
    display:flex; align-items:center; justify-content:center; margin-top:.15rem;
  }
  .ex-text{ font-size:1.55rem; line-height:1.6; }
  .hl{ color:var(--red); font-weight:700; }

  /* ---- 出處／近反義詞／易錯提醒 ---- */
  .chip-row{ display:flex; gap:2.6rem; margin-bottom:1.6rem; flex-wrap:wrap; }
  .chip-block{ flex:1 1 40%; }
  .chips{ font-size:1.4rem; color:var(--ink); }
  .warn{
    background:var(--warnbg); color:var(--warnfg);
    border-radius:1rem; padding:1.2rem 1.6rem;
    font-size:1.3rem; line-height:1.6;
  }

  /* ---- 複習分隔頁 ---- */
  .divider{ display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; }
  .divider-label{ font-size:3.4rem; font-weight:700; color:var(--red); }
  .divider-sub{ font-size:1.4rem; color:var(--gray); margin-top:1.2rem; }

  /* ---- 複習卡 ---- */
  .review-wrap{ display:flex; flex-direction:column; align-items:center; text-align:center; margin-top:2vh; }
  .review-ch{ font-size:5.4rem; font-weight:700; color:var(--ink); }
  .review-zh{ font-size:1.5rem; color:var(--gold); margin-top:1rem; }
  .review-explain{ font-size:1.6rem; color:var(--ink); margin-top:2rem; max-width:80vw; line-height:1.6; }

  /* ---- 待機畫面 ---- */
  .idle{ display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center; }
  .idle-time{ font-size:6rem; font-weight:700; color:var(--gray); letter-spacing:.05em; }
  .idle-msg{ font-size:1.5rem; color:var(--ink); margin-top:1.8rem; }
  .idle-reason{ font-size:1.2rem; color:var(--gray); margin-top:.8rem; }

  /* ---- 底部進度條 ---- */
  .progressbar{
    position:fixed; left:1.9rem; right:1.9rem; bottom:1.9rem;
    height:.35rem; background:#EDE4D2; border-radius:999px; overflow:hidden; z-index:6;
  }
  .progressbar-fill{ height:100%; width:0%; background:var(--gold); }
  .progressbar-fill.run{ transition:width linear; }
</style>
</head>
<body>
  <div id="stage" class="stage"></div>
  <div class="progressbar"><div class="progressbar-fill" id="pbfill"></div></div>

  <script id="data-idioms" type="application/json">__IDIOMS_JSON__</script>
  <script id="data-schedule" type="application/json">__SCHEDULE_JSON__</script>

  <script>
  (function(){
    "use strict";
    const IDIOMS   = JSON.parse(document.getElementById("data-idioms").textContent);
    const SCHEDULE = JSON.parse(document.getElementById("data-schedule").textContent);
    const stage  = document.getElementById("stage");
    const pbfill = document.getElementById("pbfill");
    const params = new URLSearchParams(location.search);
    const DEMO   = params.has("demo");

    // 離線快取：只有從網站開啟時才註冊（file:// 開啟時略過）。
    // 成功載入過一次之後，就算學校早上網路不通也能照常播放。
    if ("serviceWorker" in navigator && location.protocol.indexOf("http") === 0) {
      navigator.serviceWorker.register("sw.js").catch(function(){ /* 註冊失敗不影響播放 */ });
    }

    // 播放期間不讓螢幕休眠（大螢幕/投影機用途）；不支援或被拒絕就靜默略過，不影響輪播本身。
    let wakeLock = null;
    function ensureWakeLock(){
      if (!("wakeLock" in navigator) || wakeLock) return;
      navigator.wakeLock.request("screen").then(function(lock){
        wakeLock = lock;
        wakeLock.addEventListener("release", function(){ wakeLock = null; });
      }).catch(function(){ /* 忽略：例如非安全環境或裝置不支援 */ });
    }
    document.addEventListener("visibilitychange", function(){
      if (document.visibilityState === "visible" && mode === "deck") ensureWakeLock();
    });

    function pad(n){ return String(n).padStart(2,"0"); }
    function dateStr(d){ return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate()); }
    function hm(d){ return pad(d.getHours())+":"+pad(d.getMinutes()); }
    function parseHM(s){ const p=(s||"").split(":").map(Number); return (p[0]||0)*60+(p[1]||0); }

    function isSchoolDay(d){
      const day = d.getDay();
      if (day===0 || day===6) return {ok:false, reason:"週末"};
      const ds = dateStr(d);
      const range = SCHEDULE.學期起訖;
      if (range && range.開始 && range.結束 && (ds < range.開始 || ds > range.結束)) {
        return {ok:false, reason:"不在學期範圍內"};
      }
      const off = (SCHEDULE.停課日||[]).find(function(x){ return x.日期===ds; });
      if (off) return {ok:false, reason: off.說明 || "停課日"};
      return {ok:true, reason:null};
    }

    function inPlayWindow(d){
      const nowM = d.getHours()*60 + d.getMinutes();
      const startM = parseHM(SCHEDULE.播放時段 && SCHEDULE.播放時段.開始 || "07:30");
      const endM   = parseHM(SCHEDULE.播放時段 && SCHEDULE.播放時段.結束 || "08:30");
      return nowM >= startM && nowM < endM;
    }

    function shuffle(arr){
      for (let i=arr.length-1;i>0;i--){
        const j = Math.floor(Math.random()*(i+1));
        const t = arr[i]; arr[i]=arr[j]; arr[j]=t;
      }
      return arr;
    }

    function escapeHtml(s){
      return String(s==null?"":s)
        .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    }

    function highlight(sentence, idiom){
      const safeIdiom = escapeHtml(idiom);
      return escapeHtml(sentence).split(safeIdiom).join('<span class="hl">'+safeIdiom+'</span>');
    }

    function renderTitle(idiom, tag){
      const chars = Array.from(idiom.成語||"");
      const zh = (idiom.注音||"").split(/\s+/).filter(Boolean);
      let glyphs;
      if (chars.length && chars.length===zh.length){
        glyphs = chars.map(function(c,i){
          return '<div class="glyph"><div class="zh">'+escapeHtml(zh[i])+'</div><div class="ch">'+escapeHtml(c)+'</div></div>';
        }).join("");
        glyphs = '<div class="glyphs">'+glyphs+'</div>';
      } else {
        glyphs = '<div class="glyph-fallback"><div class="ch-line">'+escapeHtml(idiom.成語)+'</div>'
               + '<div class="zh-line">'+escapeHtml(idiom.注音||"")+'</div></div>';
      }
      return '<div class="tag">'+escapeHtml(tag)+'</div>'
           + '<div class="title-wrap">'+glyphs
           + '<div class="pinyin">'+escapeHtml(idiom.拼音||"")+'</div></div>';
    }

    function renderMeaning(idiom, tag){
      const rows = (idiom.字義||[]).map(function(m){
        return '<div class="mrow"><div class="mchar">'+escapeHtml(m.字)+'</div><div class="mdesc">'+escapeHtml(m.義)+'</div></div>';
      }).join("");
      return '<div class="tag">'+escapeHtml(tag)+'</div>'
           + '<div class="heading">'+escapeHtml(idiom.成語)+'<span class="heading-sub">・字義拆解</span></div>'
           + '<div class="mgrid">'+rows+'</div>';
    }

    function renderExplain(idiom, tag){
      return '<div class="tag">'+escapeHtml(tag)+'</div>'
           + '<div class="heading">'+escapeHtml(idiom.成語)+'<span class="heading-sub">・解釋</span></div>'
           + '<div class="block"><div class="label">解釋</div><div class="text-lg">'+escapeHtml(idiom.解釋||"")+'</div></div>'
           + '<div class="block"><div class="label">白話一點說</div><div class="text-lg muted">'+escapeHtml(idiom.白話解釋||"")+'</div></div>';
    }

    function renderExamples(idiom, tag){
      const items = (idiom.例句||[]).map(function(s,i){
        return '<div class="ex-row"><div class="ex-num">'+(i+1)+'</div><div class="ex-text">'+highlight(s, idiom.成語)+'</div></div>';
      }).join("");
      return '<div class="tag">'+escapeHtml(tag)+'</div>'
           + '<div class="heading">'+escapeHtml(idiom.成語)+'<span class="heading-sub">・例句</span></div>'
           + '<div class="ex-list">'+items+'</div>';
    }

    function renderExtra(idiom, tag){
      const near = (idiom.近義詞||[]).join("、");
      const anti = (idiom.反義詞||[]).join("、");
      let chips = "";
      if (near || anti){
        chips = '<div class="chip-row">'
          + (near ? '<div class="chip-block"><div class="label">近義詞</div><div class="chips">'+escapeHtml(near)+'</div></div>' : "")
          + (anti ? '<div class="chip-block"><div class="label">反義詞</div><div class="chips">'+escapeHtml(anti)+'</div></div>' : "")
          + '</div>';
      }
      return '<div class="tag">'+escapeHtml(tag)+'</div>'
           + '<div class="heading">'+escapeHtml(idiom.成語)+'<span class="heading-sub">・補充</span></div>'
           + (idiom.出處 ? '<div class="block"><div class="label">出處</div><div class="text-md">'+escapeHtml(idiom.出處)+'</div></div>' : "")
           + chips
           + (idiom.易錯提醒 ? '<div class="warn">⚠️ '+escapeHtml(idiom.易錯提醒)+'</div>' : "");
    }

    function renderDivider(){
      return '<div class="divider"><div class="divider-label">複習時間</div>'
           + '<div class="divider-sub">一起再唸一次前面學過的成語</div></div>';
    }

    function renderReview(idiom){
      return '<div class="tag tag-review">複習・'+escapeHtml(idiom.課次||"")+'</div>'
           + '<div class="review-wrap">'
           + '<div class="review-ch">'+escapeHtml(idiom.成語)+'</div>'
           + '<div class="review-zh">'+escapeHtml(idiom.注音||"")+'</div>'
           + '<div class="review-explain">'+escapeHtml(idiom.解釋||"")+'</div>'
           + '</div>';
    }

    function buildDeck(){
      const list = IDIOMS.成語 || [];
      if (!list.length) return [];
      const todayId = IDIOMS.今日編號;
      let todayIdx = todayId ? list.findIndex(function(x){ return x.編號===todayId; }) : -1;
      if (todayIdx < 0) todayIdx = list.length - 1;
      const today = list[todayIdx];
      const tag = (IDIOMS.科目||"國語") + "．" + (today.課次||"") + "．今日成語";
      const others = list.filter(function(_,i){ return i!==todayIdx; });
      shuffle(others);

      const deck = [
        { render:function(){ return renderTitle(today, tag); },   dur:8000  },
        { render:function(){ return renderMeaning(today, tag); }, dur:10000 },
        { render:function(){ return renderExplain(today, tag); }, dur:10000 },
        { render:function(){ return renderExamples(today, tag); }, dur:13000 },
        { render:function(){ return renderExtra(today, tag); },   dur:12000 }
      ];
      if (others.length){
        deck.push({ render:renderDivider, dur:3500 });
        others.forEach(function(o){
          deck.push({ render:function(){ return renderReview(o); }, dur:7000 });
        });
      }
      return deck;
    }

    let deck = [], idx = 0, timer = null, pbTimer = null, mode = null;

    function runProgressBar(duration){
      pbfill.classList.remove("run");
      pbfill.style.transition = "none";
      pbfill.style.width = "0%";
      // 強制 reflow 讓下一次的 transition 生效
      void pbfill.offsetWidth;
      clearTimeout(pbTimer);
      pbTimer = setTimeout(function(){
        pbfill.style.transition = "width "+duration+"ms linear";
        pbfill.classList.add("run");
        pbfill.style.width = "100%";
      }, 30);
    }

    function showSlide(){
      if (!deck.length){
        fadeIn('<div class="idle"><div class="idle-msg">尚未建立任何成語資料，請先更新 data/成語資料.json</div></div>');
        pbfill.style.width = "0%";
        return;
      }
      const slide = deck[idx];
      fadeIn(slide.render());
      runProgressBar(slide.dur);
      clearTimeout(timer);
      timer = setTimeout(advance, slide.dur);
    }

    function advance(){
      idx++;
      if (idx >= deck.length){ idx = 0; deck = buildDeck(); }
      showSlide();
    }

    // 字數多的成語（例如「醉翁之意不在酒」）或比較窄的螢幕，大字可能會超出畫面寬度。
    // 這裡量完真實寬度後按比例縮小，確保任何字數、任何解析度都不會被切到。
    // 注意：剛換頁的那一個 frame 有時還沒完成版面配置，量到的寬度會是 0，
    // 這時不能判定「沒有超出」，必須等下一個 frame 重量，否則會漏縮放。
    function fitToWidth(attempt){
      attempt = attempt || 0;
      const cs = getComputedStyle(stage);
      const avail = stage.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      if (!(avail > 0)) return;
      const targets = stage.querySelectorAll(".glyphs, .glyph-fallback .ch-line, .review-ch");
      let notLaidOut = false;
      targets.forEach(function(el){
        el.style.transform = "";
        const w = el.scrollWidth;
        if (w === 0) { notLaidOut = true; return; }
        if (w > avail) {
          el.style.transformOrigin = "center center";
          el.style.transform = "scale(" + (avail / w).toFixed(3) + ")";
        }
      });
      if (notLaidOut && attempt < 10) {
        setTimeout(function(){ fitToWidth(attempt + 1); }, 50);
      }
    }

    function fadeIn(html){
      stage.classList.remove("show");
      void stage.offsetWidth;
      stage.innerHTML = html;
      // 這裡刻意用 setTimeout 而不是 requestAnimationFrame：視窗被遮蔽或最小化時
      // rAF 會停擺，.show 就永遠加不上去、畫面整片空白，而換頁的計時器還在跑。
      // setTimeout 在背景仍會執行，畫面不會卡在全黑。
      setTimeout(function(){
        fitToWidth();
        stage.classList.add("show");
      }, 20);
    }

    window.addEventListener("resize", fitToWidth);

    function renderIdleScreen(reason){
      const startT = (SCHEDULE.播放時段 && SCHEDULE.播放時段.開始) || "07:30";
      const endT   = (SCHEDULE.播放時段 && SCHEDULE.播放時段.結束) || "08:30";
      fadeIn('<div class="idle"><div class="idle-time" id="idleClock">--:--</div>'
        + '<div class="idle-msg">成語卡播放時間：每個上課日 '+startT+'–'+endT+'</div>'
        + (reason ? '<div class="idle-reason">今天不播放（'+escapeHtml(reason)+'）</div>' : '')
        + '</div>');
      pbfill.classList.remove("run");
      pbfill.style.transition = "none";
      pbfill.style.width = "0%";
    }

    function updateIdleClock(now){
      const el = document.getElementById("idleClock");
      if (el) el.textContent = hm(now);
    }

    function tick(){
      const now = new Date();
      const school = isSchoolDay(now);
      const playable = DEMO || (school.ok && inPlayWindow(now));

      if (playable){
        if (mode !== "deck"){
          mode = "deck";
          deck = buildDeck();
          idx = 0;
          showSlide();
          ensureWakeLock();
        }
      } else {
        if (mode !== "idle"){
          mode = "idle";
          clearTimeout(timer);
          clearTimeout(pbTimer);
          renderIdleScreen(school.ok ? null : school.reason);
        }
        updateIdleClock(now);
      }
    }

    tick();
    setInterval(tick, 1000);
  })();
  </script>
</body>
</html>
"""


def main():
    idioms = json.load(open(DATA, encoding="utf-8"))
    schedule = json.load(open(SCHEDULE, encoding="utf-8"))

    html = HTML_TEMPLATE.replace(
        "__IDIOMS_JSON__", json.dumps(idioms, ensure_ascii=False)
    ).replace(
        "__SCHEDULE_JSON__", json.dumps(schedule, ensure_ascii=False)
    )

    # 本機版（備援／離線預覽用）
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    # GitHub Pages 版：同一份 HTML + 離線快取 + 給排程腳本抓的設定檔
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(DOCS_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    with open(DOCS_SW, "w", encoding="utf-8") as f:
        f.write(SERVICE_WORKER)
    with open(DOCS_CFG, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    total = len(idioms.get("成語", []))
    today = idioms.get("今日編號")
    today_label = today if today else (idioms["成語"][-1]["編號"] + "（陣列最後一筆，預設）" if total else "（無資料）")
    print(f"已產生播放頁，共 {total} 則成語")
    print(f"  本機版 → {OUT}")
    print(f"  線上版 → {DOCS_HTML}（推上 GitHub 後由 Pages 服務）")
    print(f"今日成語：{today_label}")
    print(f"播放時段：{schedule.get('播放時段',{}).get('開始','07:30')}–{schedule.get('播放時段',{}).get('結束','08:30')}")
    print("本機預覽：瀏覽器打開 output/播放/index.html，網址後面加 ?demo=1 可略過時間判斷、強制輪播。")


if __name__ == "__main__":
    main()
