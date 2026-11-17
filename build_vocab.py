#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _vocab/items.json 打包成单文件交互页 成语记忆.html"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "_vocab" / "items.json"
OUT = HERE / "成语记忆.html"

BAD_CHARS = re.compile(r"[^\u4e00-\u9fa5，。、；：？！“”‘’（）《》…—·A-Za-z0-9%+\-,()]")
ASCII_FIX = {",": "，", "(": "（", ")": "）", ";": "；", ":": "：", "?": "？", "!": "！"}


def clean_items(raw: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for r in raw:
        w = (r.get("w") or "").strip()
        d = (r.get("d") or "").strip()
        if not re.fullmatch(r"[\u4e00-\u9fa5]{2,8}", w):
            continue
        if len(d) < 6 or w in seen:
            continue
        # 常见 OCR 噪音：页眉标题混入、重复括号、行首标点
        d = re.sub(r"^高频成语积累800词?记忆?版", "", d)
        d = re.sub(r"^解释", "", d)
        d = d.replace("（(", "（").replace("(（", "（").replace("))", "）")
        d = re.sub(r"^[，。、；：]", "", d)
        d = BAD_CHARS.sub("", d)
        for a, b in ASCII_FIX.items():
            d = d.replace(a, b)
        if len(d) < 6:
            continue
        # 释义里夹带的修订批注去掉，避免干扰阅读
        d = d.replace("（删除）", "").replace("(删除)", "").replace("（修改）", "")
        seen.add(w)
        out.append({"w": w, "d": d})
    # 四字成语排前面，其次两字词，再按字面
    out.sort(key=lambda x: (0 if len(x["w"]) == 4 else (1 if len(x["w"]) == 2 else 2), x["w"]))
    return out


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>高频成语速记</title>
<style>
:root{
  --ink:#111827; --sub:#6b7280; --line:#e6e8ec; --bg:#f5f6f8;
  --card:#fff; --accent:#b45309; --gold:#f59e0b;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:15px;line-height:1.7}
header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
.htop{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:14px 0 10px}
.brand{font-size:17px;font-weight:700;letter-spacing:.3px}
.brand small{display:block;font-size:11.5px;font-weight:400;color:var(--sub);margin-top:3px;letter-spacing:0}
.hstat{text-align:right;font-size:12px;color:var(--sub);white-space:nowrap}
.xlink{font-size:11px;font-weight:600;color:#b45309;text-decoration:none;margin-left:9px;
  border:1px solid #fde68a;background:#fffbeb;padding:1px 7px;border-radius:8px;vertical-align:2px}
.xlink:hover{background:#fef3c7}
.hstat b{font-size:17px;color:var(--ink);font-variant-numeric:tabular-nums}
.hstat .fav{color:var(--accent)}
.sync{display:inline-block;margin-top:3px;font-size:10.5px;padding:1px 7px;border-radius:9px;
  border:1px solid var(--line);color:#9ca3af;background:#fafafa}
.sync.ok{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.sync.off{color:#b91c1c;border-color:#fecaca;background:#fef2f2}

.bar{display:flex;gap:8px;align-items:center;padding-bottom:10px;flex-wrap:wrap}
.search{flex:1;min-width:150px;position:relative}
.search input{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:10px;
  font-size:14px;background:#fff;outline:none}
.search input:focus{border-color:#c7cdd6;box-shadow:0 0 0 3px #eef1f5}
.seg{display:flex;background:#eceef2;border-radius:10px;padding:3px;gap:2px}
.seg button{border:0;background:transparent;padding:6px 12px;border-radius:8px;font-size:13px;
  color:var(--sub);cursor:pointer;font-family:inherit}
.seg button.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.06)}
.chips{display:flex;gap:6px;overflow-x:auto;padding:0 0 10px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid var(--line);background:#fff;color:var(--sub);
  padding:5px 11px;border-radius:999px;font-size:12.5px;cursor:pointer;font-family:inherit;white-space:nowrap}
.chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}

main{max-width:760px;margin:0 auto;padding:18px 16px 120px}

/* 卡片模式 */
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:26px 22px 20px;box-shadow:0 1px 2px rgba(16,24,40,.04);position:relative;min-height:260px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;cursor:pointer}
.card .word{font-size:42px;font-weight:700;letter-spacing:6px;line-height:1.4;padding-left:6px}
.card .hintline{margin-top:18px;font-size:12.5px;color:#9ca3af}
.card .def{display:none;margin-top:16px;font-size:15.5px;line-height:1.95;color:#1f2937;
  text-align:left;width:100%;border-top:1px dashed var(--line);padding-top:16px}
.card.open .def{display:block}
.card.open .hintline{display:none}
.card .tagrow{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px;width:100%}
.card .tagrow span{font-size:11px;color:var(--sub);background:#f3f4f6;border-radius:6px;padding:2px 8px}
.star{position:absolute;top:14px;right:16px;width:38px;height:38px;border-radius:50%;border:0;
  background:transparent;font-size:22px;line-height:1;color:#d1d5db;cursor:pointer}
.star.on{color:var(--gold)}
.nav{display:flex;gap:10px;align-items:center;margin-top:14px}
.nav .btn{flex:1;padding:11px;border-radius:11px;border:1px solid var(--line);background:#fff;
  font-size:14px;color:var(--ink);cursor:pointer;font-family:inherit}
.nav .btn:disabled{color:#c7cbd1}
.nav .btn.main{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
.pos{text-align:center;font-size:12px;color:var(--sub);margin-top:10px}

/* 全览模式 */
.grid{display:grid;gap:10px}
.item{background:#fff;border:1px solid var(--line);border-radius:13px;padding:13px 14px;
  position:relative;cursor:pointer}
.item .w{font-size:17px;font-weight:700;letter-spacing:1px;padding-right:26px}
.item .d{font-size:13.5px;line-height:1.85;color:#374151;margin-top:5px}
.item .s{font-size:11px;color:#9ca3af;margin-top:6px}
.item .k{position:absolute;top:9px;right:11px;font-size:16px;color:#d1d5db}
.item .k.on{color:var(--gold)}
.item.clip .d{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.empty{text-align:center;color:#9ca3af;font-size:13.5px;padding:60px 0}
.foot{max-width:760px;margin:0 auto;padding:0 16px 40px;text-align:center;font-size:11.5px;color:#9ca3af;line-height:1.8}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <div class="htop">
      <div class="brand">高频成语速记<a class="xlink" href="省考平台.html#quiz">每日刷题 ↗</a><small id="sub"></small></div>
      <div class="hstat">
        <div><b id="totalN">0</b> 条　<span class="fav" id="favN">★ 0</span></div>
        <span class="sync" id="sync">连接中…</span>
      </div>
    </div>
    <div class="bar">
      <div class="search"><input id="q" type="search" placeholder="搜成语或释义里的字…" autocomplete="off"></div>
      <div class="seg">
        <button id="mCard" class="on">卡片</button>
        <button id="mList">全览</button>
      </div>
    </div>
    <div class="chips" id="chips"></div>
  </div>
</header>

<main>
  <section id="cardView">
    <div class="card" id="card">
      <button class="star" id="star" title="收藏（F）">☆</button>
      <div class="word" id="word">—</div>
      <div class="hintline">点击卡片看释义　·　空格翻面</div>
      <div class="def" id="def"></div>
      <div class="tagrow" id="tags"></div>
    </div>
    <div class="nav">
      <button class="btn" id="prev">上一个</button>
      <button class="btn main" id="next">下一个</button>
    </div>
    <div class="nav">
      <button class="btn" id="shuffle">随机一条</button>
      <button class="btn" id="reveal">显示释义</button>
    </div>
    <div class="pos" id="pos"></div>
  </section>

  <section id="listView" style="display:none">
    <div class="grid" id="grid"></div>
    <div class="empty" id="empty" style="display:none">没有符合条件的成语</div>
  </section>
</main>

<p class="foot">释义整理自《高频800词记忆版》，OCR 提取后人工校验；★ 收藏存在本地服务器，换浏览器也不会丢</p>

<script>
const DATA = __DATA__;
const API = 'http://127.0.0.1:8760/api/vocab';
const FKEY = 'gdvocab-favs', FUK = 'gdvocab-updated';
const $ = s => document.querySelector(s);

let favs = {};
try { favs = JSON.parse(localStorage.getItem(FKEY) || '{}'); } catch(e){ favs = {}; }
let localAt = Number(localStorage.getItem(FUK) || 0) || 0;

let mode = 'card';
let filter = 'all';
let kw = '';
let list = [];
let pos = 0;
let opened = false;

/* ---------- 同步 ---------- */
let pushTimer = null, retryTimer = null, pushing = false;

function setSync(state, msg){
  const el = $('#sync');
  el.className = 'sync ' + state;
  el.textContent = msg;
}

function saveLocal(){
  try{
    localStorage.setItem(FKEY, JSON.stringify(favs));
    localStorage.setItem(FUK, String(localAt));
  }catch(e){}
}

function save(){
  localAt = Date.now();
  saveLocal();
  clearTimeout(pushTimer);
  pushTimer = setTimeout(push, 350);
}

function push(){
  if(pushing){ retryTimer = setTimeout(push, 800); return; }
  pushing = true;
  fetch(API, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ answers:{}, favs, updatedAt: localAt })
  })
  .then(r => r.json())
  .then(res => {
    pushing = false;
    clearTimeout(retryTimer);
    if(res && res.stale){ adopt(res); setSync('ok','已同步'); return; }
    setSync('ok','已同步 ' + new Date().toLocaleTimeString('zh-CN',{hour12:false}));
  })
  .catch(() => {
    pushing = false;
    setSync('off','未连服务器');
    clearTimeout(retryTimer);
    retryTimer = setTimeout(push, 8000);
  });
}

function adopt(snap){
  favs = (snap && snap.favs && typeof snap.favs === 'object') ? snap.favs : {};
  localAt = Number(snap && snap.updatedAt || 0) || 0;
  saveLocal();
  buildChips();
  build(); render();
}

function pull(){
  fetch(API + '?t=' + Date.now(), {cache:'no-store'})
    .then(r => { if(!r.ok) throw 0; return r.json(); })
    .then(snap => {
      const remoteAt = Number(snap.updatedAt || 0) || 0;
      if(remoteAt > localAt + 500){
        adopt(snap);
        setSync('ok','已同步');
      } else {
        setSync('ok','已同步 ' + new Date().toLocaleTimeString('zh-CN',{hour12:false}));
        if(localAt > remoteAt) save();
      }
    })
    .catch(() => setSync('off','未连服务器'));
}

/* ---------- 列表构建 ---------- */
function build(){
  list = DATA.filter(it => {
    if(filter === 'fav' && !favs[it.w]) return false;
    if(filter === 'len4' && it.w.length !== 4) return false;
    if(filter === 'len2' && it.w.length !== 2) return false;
    if(filter === 'other' && (it.w.length === 4 || it.w.length === 2)) return false;
    if(kw){
      const k = kw.toLowerCase();
      if(!(it.w.includes(kw) || it.d.toLowerCase().includes(k))) return false;
    }
    return true;
  });
  if(pos > list.length - 1) pos = 0;
}

function buildChips(){
  const box = $('#chips');
  box.innerHTML = '';
  const cats = [
    ['all', '全部 ' + DATA.length],
    ['fav', '★ 收藏 ' + Object.keys(favs).length],
    ['len4', '四字成语'],
    ['len2', '两字词'],
    ['other', '其他']
  ];
  cats.forEach(([c, label]) => {
    const b = document.createElement('button');
    b.className = 'chip' + (filter === c ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { filter = c; pos = 0; buildChips(); build(); render(); };
    box.appendChild(b);
  });
}

/* ---------- 渲染 ---------- */
function render(){
  $('#totalN').textContent = DATA.length;
  $('#favN').textContent = '★ ' + Object.keys(favs).length;
  const names = {all:'全部', fav:'只看收藏', len4:'四字成语', len2:'两字词', other:'其他长度'};
  $('#sub').textContent = names[filter] || '全部';

  if(mode === 'card'){ $('#cardView').style.display = ''; $('#listView').style.display = 'none'; renderCard(); }
  else { $('#cardView').style.display = 'none'; $('#listView').style.display = ''; renderList(); }
}

function renderCard(){
  const it = list[pos];
  const card = $('#card');
  if(!it){
    $('#word').textContent = '—';
    $('#def').textContent = '';
    $('#tags').innerHTML = '';
    $('#pos').textContent = '没有符合条件的成语';
    $('#star').style.visibility = 'hidden';
    card.classList.remove('open');
    return;
  }
  $('#star').style.visibility = 'visible';
  const on = !!favs[it.w];
  $('#star').textContent = on ? '★' : '☆';
  $('#star').classList.toggle('on', on);

  $('#word').textContent = it.w;
  $('#def').textContent = it.d;
  const kind = it.w.length === 4 ? '四字成语' : (it.w.length === 2 ? '两字词' : it.w.length + ' 字');
  $('#tags').innerHTML = '<span></span>';
  $('#tags').querySelector('span').textContent = kind;

  card.classList.toggle('open', opened);
  $('#pos').textContent = (pos + 1) + ' / ' + list.length;
}

function renderList(){
  const g = $('#grid');
  g.innerHTML = '';
  $('#empty').style.display = list.length ? 'none' : '';
  const frag = document.createDocumentFragment();
  list.forEach((it, i) => {
    const d = document.createElement('div');
    d.className = 'item clip';
    const on = !!favs[it.w];
    d.innerHTML = '<div class="w"></div><div class="d"></div>' +
                  '<span class="k' + (on ? ' on' : '') + '">' + (on ? '★' : '☆') + '</span>';
    d.querySelector('.w').textContent = it.w;
    d.querySelector('.d').textContent = it.d;
    d.onclick = e => {
      if(e.target.classList.contains('k')){ toggleFav(it.w); return; }
      d.classList.toggle('clip');
    };
    frag.appendChild(d);
  });
  g.appendChild(frag);
}

function toggleFav(w){
  if(favs[w]) delete favs[w]; else favs[w] = 1;
  save();
  buildChips();
  if(filter === 'fav'){ build(); if(pos > list.length - 1) pos = Math.max(0, list.length - 1); }
  render();
}

/* ---------- 交互 ---------- */
function go(step){
  if(!list.length) return;
  pos = (pos + step + list.length) % list.length;
  opened = false;
  renderCard();
}

function randomOne(){
  if(!list.length) return;
  pos = Math.floor(Math.random() * list.length);
  opened = false;
  renderCard();
}

$('#card').onclick = e => {
  if(e.target.id === 'star') return;
  opened = !opened;
  $('#card').classList.toggle('open', opened);
};
$('#star').onclick = e => { e.stopPropagation(); if(list[pos]) toggleFav(list[pos].w); };
$('#prev').onclick = () => go(-1);
$('#next').onclick = () => go(1);
$('#shuffle').onclick = randomOne;
$('#reveal').onclick = () => { opened = !opened; $('#card').classList.toggle('open', opened); };

$('#mCard').onclick = () => { mode = 'card'; $('#mCard').classList.add('on'); $('#mList').classList.remove('on'); render(); };
$('#mList').onclick = () => { mode = 'list'; $('#mList').classList.add('on'); $('#mCard').classList.remove('on'); render(); };

$('#q').oninput = e => { kw = e.target.value.trim(); pos = 0; build(); render(); };

document.addEventListener('keydown', e => {
  if(e.target.tagName === 'INPUT') return;
  const k = e.key;
  if(k === 'ArrowLeft') go(-1);
  else if(k === 'ArrowRight') go(1);
  else if(k === ' '){ e.preventDefault(); opened = !opened; $('#card').classList.toggle('open', opened); }
  else if(k === 'f' || k === 'F'){ if(list[pos]) toggleFav(list[pos].w); }
});

buildChips();
build();
render();
pull();
setInterval(pull, 60000);
document.addEventListener('visibilitychange', () => { if(!document.hidden) pull(); });
</script>
</body>
</html>
"""


def main() -> None:
    if not SRC.exists():
        sys.exit(f"缺少 {SRC}，先跑 extract_vocab.py")
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    items = clean_items(raw)
    data = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.replace("__DATA__", data)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK  {len(items)} 条 -> {OUT}")


if __name__ == "__main__":
    main()
