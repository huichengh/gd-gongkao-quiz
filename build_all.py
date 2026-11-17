#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把题库目录下所有分期的 Markdown 合并成一个刷题总入口 HTML。

用法：
    python build_all.py [输出.html]

特性：
    - 顶部按日期切换期数
    - 收藏跨期汇总，可定位回原期
    - 答题记录、收藏各存一份，旧版单期记录会自动迁移
"""
import glob
import json
import pathlib
import re
import sys

from build_quiz import build_sections, parse

HERE = pathlib.Path(__file__).parent

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
:root{
  --bg:#f4f5f7; --card:#fff; --ink:#15181f; --sub:#6b7280; --line:#e6e8ec;
  --primary:#2563eb; --primary-soft:#eff4ff;
  --ok:#15803d; --ok-bg:#f0fdf4; --ok-line:#86efac;
  --bad:#b91c1c; --bad-bg:#fef2f2; --bad-line:#fca5a5;
  --shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px rgba(16,24,40,.06);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--ink); font-size:16px; line-height:1.6;
  font-family:"Microsoft YaHei","微软雅黑",-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
  padding-bottom:96px;
}
.wrap{max-width:820px;margin:0 auto;padding:0 16px}

header{
  position:sticky;top:0;z-index:30;background:rgba(244,245,247,.94);
  backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line);
}
.htop{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 0 8px}
.brand{font-size:16px;font-weight:650;letter-spacing:.2px}
.brand small{display:block;font-weight:400;font-size:12px;color:var(--sub);margin-top:2px;letter-spacing:0}
.hstat{text-align:right;font-size:12px;color:var(--sub);white-space:nowrap}
.xlink{font-size:11px;font-weight:600;color:#b45309;text-decoration:none;margin-left:9px;
  border:1px solid #fde68a;background:#fffbeb;padding:1px 7px;border-radius:8px;vertical-align:2px}
.xlink:hover{background:#fef3c7}
.hstat b{font-size:18px;color:var(--ink);font-variant-numeric:tabular-nums}
.hstat .rate{font-weight:600;font-variant-numeric:tabular-nums}
.hstat .fav{color:#b45309}
.sync{display:inline-block;margin-top:3px;font-size:10.5px;line-height:1.5;padding:1px 7px;border-radius:9px;border:1px solid #e5e7eb;color:#9ca3af;background:#fafafa}
.sync.ok{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.sync.off{color:#b91c1c;border-color:#fecaca;background:#fef2f2}
.pbar{height:3px;background:#e3e5ea;overflow:hidden}
.pbar i{display:block;height:100%;width:0;background:var(--primary);transition:width .35s ease}

.dates{display:flex;gap:8px;overflow-x:auto;padding:10px 0;scrollbar-width:none}
.dates::-webkit-scrollbar{display:none}
.date{
  flex:0 0 auto;border:1px solid var(--line);background:#fff;border-radius:10px;
  padding:5px 11px;cursor:pointer;line-height:1.25;text-align:center;transition:.14s;
}
.date b{display:block;font-size:13.5px;font-weight:650;color:var(--ink);font-variant-numeric:tabular-nums}
.date small{font-size:10px;color:#9ca3af}
.date:hover{border-color:#c3c9d4}
.date.on{background:var(--ink);border-color:var(--ink)}
.date.on b{color:#fff}
.date.on small{color:#a9afba}

.tabs{display:flex;gap:8px;overflow-x:auto;padding:0 0 12px;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{
  flex:0 0 auto;border:1px solid var(--line);background:#fff;color:#4b5563;
  padding:6px 13px;border-radius:999px;font-size:13px;cursor:pointer;white-space:nowrap;transition:.15s;
}
.tab:hover{border-color:#c9ced8}
.tab.on{background:var(--ink);border-color:var(--ink);color:#fff}

.qcard{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:22px 22px 18px}
.qmeta{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--sub);margin-bottom:12px;flex-wrap:wrap}
.qmeta .no{font-weight:600;color:var(--primary);background:var(--primary-soft);padding:2px 9px;border-radius:6px;font-variant-numeric:tabular-nums}
.qmeta .sec{padding:2px 9px;background:#f3f4f6;border-radius:6px}
.qmeta .from{padding:2px 9px;background:#fff7ed;color:#b45309;border-radius:6px;font-weight:550}
.star{
  margin-left:auto;background:none;border:0;padding:2px 6px;border-radius:7px;
  font-size:19px;line-height:1;color:#c3c8d2;cursor:pointer;transition:.15s;font-family:inherit;
}
.star:hover{background:#f3f4f6;color:#f59e0b}
.star.on{color:#f59e0b}
.qtext{font-size:17px;line-height:1.8;font-weight:500;letter-spacing:.1px;margin-bottom:18px}
.opts{display:flex;flex-direction:column;gap:10px}
.opt{
  display:flex;gap:12px;align-items:flex-start;width:100%;text-align:left;
  background:#fff;border:1.5px solid var(--line);border-radius:11px;
  padding:12px 14px;font-size:15.5px;line-height:1.65;color:var(--ink);
  cursor:pointer;transition:.14s;font-family:inherit;
}
.opt:hover:not(.done){border-color:#b9c2d0;background:#fafbfc}
.opt .k{
  flex:0 0 24px;height:24px;border-radius:50%;background:#f1f2f4;color:#4b5563;
  font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center;
  margin-top:1px;transition:.14s;
}
.opt .t{flex:1}
.opt.correct{border-color:var(--ok-line);background:var(--ok-bg)}
.opt.correct .k{background:var(--ok);color:#fff}
.opt.wrong{border-color:var(--bad-line);background:var(--bad-bg)}
.opt.wrong .k{background:var(--bad);color:#fff}
.opt.dim{opacity:.62}
.opt.done{cursor:default}

.exp{margin-top:18px;border-top:1px dashed var(--line);padding-top:16px;display:none}
.exp.show{display:block;animation:fade .22s ease}
@keyframes fade{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.verdict{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600;margin-bottom:10px;padding:6px 11px;border-radius:8px;width:fit-content}
.verdict.ok{color:#166534;background:#dcfce7}
.verdict.bad{color:#b91c1c;background:#fee2e2}
.verdict .badge{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px;background:rgba(255,255,255,.75);color:#4b5563}
.expline{display:flex;gap:8px;align-items:flex-start;margin-bottom:6px}
.expline .lbl{flex:0 0 auto;font-size:11.5px;font-weight:600;color:#6b7280;background:#f3f4f6;padding:2px 7px;border-radius:5px;margin-top:2px}
.expline .val{font-size:14.5px;line-height:1.8;color:#111827}
.redo{margin-top:14px;font-size:12.5px;color:#4b5563;background:#f3f4f6;border:0;border-radius:7px;padding:6px 12px;cursor:pointer;font-family:inherit}
.redo:hover{background:#e9ebef}

footer{
  position:fixed;left:0;right:0;bottom:0;z-index:30;
  background:rgba(255,255,255,.95);backdrop-filter:blur(12px);
  border-top:1px solid var(--line);padding:10px 0 calc(10px + env(safe-area-inset-bottom));
}
.finner{max-width:820px;margin:0 auto;padding:0 16px;display:flex;align-items:center;gap:10px}
.btn{
  border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:10px;
  padding:10px 16px;font-size:14px;font-weight:550;cursor:pointer;font-family:inherit;
  transition:.14s;white-space:nowrap;
}
.btn:hover:not(:disabled){border-color:#b9c2d0;background:#fafbfc}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn.primary{background:var(--ink);color:#fff;border-color:var(--ink);flex:1}
.btn.primary:hover{background:#000}
.btn.ghost{flex:1}

.mask{position:fixed;inset:0;background:rgba(15,18,25,.42);z-index:40;display:none;align-items:flex-end;justify-content:center}
.mask.show{display:flex;animation:fade .18s ease}
.sheet{
  background:#fff;width:100%;max-width:820px;border-radius:18px 18px 0 0;
  padding:18px 18px calc(22px + env(safe-area-inset-bottom));max-height:82vh;overflow:auto;
}
.sheethead{display:flex;align-items:center;justify-content:space-between;gap:12px;position:sticky;top:0;background:#fff;padding-bottom:2px;z-index:2}
.sheet h3{margin:0;font-size:15px;font-weight:650}
.sheet .close{font-size:12.5px;color:#4b5563;background:#f3f4f6;border-radius:7px;padding:5px 11px;cursor:pointer;user-select:none}
.sheet .close:hover{background:#e9ebef}
.sheet .legend{display:flex;gap:14px;font-size:11.5px;color:var(--sub);margin:8px 0 14px;flex-wrap:wrap}
.legend i{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.grid{display:grid;grid-template-columns:repeat(10,1fr);gap:7px}
.cell{
  position:relative;aspect-ratio:1;border-radius:7px;border:1px solid var(--line);background:#fbfbfc;
  font-size:12px;color:#6b7280;display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-variant-numeric:tabular-nums;transition:.12s;
}
.cell:hover{transform:translateY(-1px)}
.cell.ok{background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok);font-weight:600}
.cell.bad{background:var(--bad-bg);border-color:var(--bad-line);color:var(--bad);font-weight:600}
.cell.cur{outline:2px solid var(--ink);outline-offset:1px}
.cell.fav::after{content:'★';position:absolute;top:0;right:2px;font-size:7.5px;color:#f59e0b;line-height:1.4}
.sheetbar{display:flex;gap:10px;margin-top:16px;position:sticky;bottom:0;background:#fff;padding:12px 0 2px;box-shadow:0 -10px 18px 6px #fff}
.sheetbar .btn{flex:1;justify-content:center}
#warnbar{background:#fffbeb;border-bottom:1px solid #fcd34d;color:#92400e;font-size:12.5px;line-height:1.7;padding:9px 16px;text-align:center}
#warnbar b{color:#78350f}
.hint{text-align:center;font-size:11.5px;color:#9ca3af;margin-top:14px;line-height:1.7}

@media (max-width:560px){
  .qcard{padding:18px 16px 14px;border-radius:14px}
  .qtext{font-size:16px}
  .opt{font-size:15px;padding:11px 12px}
  .grid{grid-template-columns:repeat(8,1fr)}
}
</style>
</head>
<body>

<div id="warnbar" style="display:none"></div>

<header>
  <div class="wrap">
    <div class="htop">
      <div class="brand">广东省考刷题<a class="xlink" href="省考平台.html#vocab">成语速记 ↗</a><small id="sub"></small></div>
      <div class="hstat">
        <div><b id="doneN">0</b> / <span id="totalN">0</span> 已答</div>
        <div>正确率 <span class="rate" id="rate">—</span>　<span class="fav" id="favN">★ 0</span></div>
        <span class="sync" id="sync">连接中…</span>
      </div>
    </div>
    <div class="dates" id="dates"></div>
  </div>
  <div class="pbar"><i id="pbar"></i></div>
  <div class="wrap"><div class="tabs" id="tabs"></div></div>
</header>

<div class="wrap">
  <main class="qcard">
    <div class="qmeta">
      <span class="no" id="qno">第 1 题</span>
      <span class="sec" id="qsec"></span>
      <span class="from" id="qfrom" style="display:none"></span>
      <button class="star" id="star" title="收藏本题（F）">☆</button>
    </div>
    <div class="qtext" id="qtext"></div>
    <div class="opts" id="opts"></div>
    <div class="exp" id="exp">
      <div class="verdict" id="verdict"></div>
      <div class="expline"><span class="lbl">考点</span><span class="val" id="tag"></span></div>
      <div class="expline"><span class="lbl">解析</span><span class="val" id="expl"></span></div>
      <button class="redo" id="redo">重做本题</button>
    </div>
  </main>

  <p class="hint">顶部切换日期换期；键盘 1—4 或 A—D 选择，← → 翻页，F 键收藏<br>做题记录存在本机浏览器里，换设备、换浏览器或换打开地址都读不到；答题卡里有「备份记录 / 恢复记录」可以把进度搬走</p>
</div>

<footer>
  <div class="finner">
    <button class="btn" id="prev">上一题</button>
    <button class="btn ghost" id="sheetBtn">答题卡</button>
    <button class="btn primary" id="next">下一题</button>
  </div>
</footer>

<div class="mask" id="mask">
  <div class="sheet">
    <div class="sheethead"><h3 id="sheetTitle">答题卡</h3><span class="close" id="closeTop">关闭</span></div>
    <div class="legend">
      <span><i style="background:#f0fdf4;border:1px solid #86efac"></i>答对</span>
      <span><i style="background:#fef2f2;border:1px solid #fca5a5"></i>答错</span>
      <span><i style="background:#fbfbfc;border:1px solid #e6e8ec"></i>未答</span>
      <span><b style="color:#f59e0b">★</b> 已收藏</span>
    </div>
    <div class="grid" id="grid"></div>
    <div class="sheetbar">
      <button class="btn" id="jumpWrong">下一道错题</button>
      <button class="btn" id="expBtn">备份记录</button>
      <button class="btn" id="impBtn">恢复记录</button>
      <button class="btn" id="resetAll">清空本页记录</button>
      <button class="btn" id="closeSheet">关闭</button>
      <input type="file" id="impFile" accept=".json,application/json" style="display:none">
    </div>
  </div>
</div>

<script>
const QUIZ = __DATA__;
const PAPERS = QUIZ.papers;

const AKEY = 'gdquiz2-answers', FKEY = 'gdquiz2-favs', MKEY = 'gdquiz2-migrated', UKEY = 'gdquiz2-updated';
const API = 'http://127.0.0.1:8760/api/progress';
const $ = s => document.querySelector(s);

let answers = {}, favs = {};
try { answers = JSON.parse(localStorage.getItem(AKEY) || '{}'); } catch(e){ answers = {}; }
try { favs = JSON.parse(localStorage.getItem(FKEY) || '{}'); } catch(e){ favs = {}; }
let localAt = Number(localStorage.getItem(UKEY) || 0) || 0;

// 存储可用性自检：某些预览环境会禁用 localStorage
const STORE_OK = (function(){
  try{
    localStorage.setItem('gdquiz2-probe','1');
    const ok = localStorage.getItem('gdquiz2-probe') === '1';
    localStorage.removeItem('gdquiz2-probe');
    return ok;
  }catch(e){ return false; }
})();

// 迁移旧版单期记录（gdquiz-<期id> 与 gdquiz-<期id>-fav）。每次都合并，幂等，不做一次性开关。
(function migrateLegacy(){
  try{
    const keys = [];
    for(let i=0;i<localStorage.length;i++) keys.push(localStorage.key(i));
    keys.forEach(k=>{
      if(!k.startsWith('gdquiz-')) return;
      const body = k.slice(7);
      let obj = {};
      try { obj = JSON.parse(localStorage.getItem(k) || '{}'); } catch(e){ return; }
      if(body.endsWith('-fav')){
        const p = body.slice(0,-4);
        if(!PAPERS.some(x=>x.id===p)) return;
        Object.keys(obj).forEach(n => { if(obj[n]) favs[p+':'+n] = 1; });
      } else {
        if(!PAPERS.some(x=>x.id===body)) return;
        Object.keys(obj).forEach(n => { if(obj[n]) answers[body+':'+n] = obj[n]; });
      }
    });
  }catch(e){}
})();

let warned = false;
function storeFail(){
  if(warned) return;
  warned = true;
  showWarn('<b>记录没存进浏览器</b>　写入被拒绝，本次作答只在内存里，刷新就丢。请点答题卡里的「备份记录」把进度导出成 json，别关页面。');
}

function saveLocalOnly(){
  try{ localStorage.setItem(AKEY, JSON.stringify(answers)); }catch(e){ storeFail(); }
  try{ localStorage.setItem(FKEY, JSON.stringify(favs)); }catch(e){ storeFail(); }
  try{ localStorage.setItem(UKEY, String(localAt)); }catch(e){}
}

function saveAll(){
  localAt = Date.now();
  saveLocalOnly();
  schedulePush();
}

/* ---------------- 与本地服务器同步 ---------------- */
let synced = false;
let pushing = false;
let pushTimer = null;
let retryTimer = null;

function setSync(state, msg){
  const el = $('#sync');
  if(!el) return;
  el.className = 'sync ' + state;
  el.textContent = msg;
  el.title = msg;
}

function schedulePush(){
  clearTimeout(pushTimer);
  pushTimer = setTimeout(pushRemote, 400);
}

function pushRemote(){
  if(pushing) { retryTimer = setTimeout(pushRemote, 800); return; }
  pushing = true;
  const body = JSON.stringify({ answers, favs, updatedAt: localAt });
  fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
    .then(r => r.json())
    .then(res => {
      pushing = false;
      clearTimeout(retryTimer);
      if(res && res.stale){
        // 服务器那份更新，反过来拉下来
        adopt(res);
        setSync('ok', '已同步');
        return;
      }
      synced = true;
      setSync('ok', '已同步 ' + new Date().toLocaleTimeString('zh-CN', {hour12:false}));
    })
    .catch(() => {
      pushing = false;
      synced = false;
      setSync('off', '未连服务器');
      clearTimeout(retryTimer);
      retryTimer = setTimeout(pushRemote, 8000);
    });
}

function adopt(snap){
  answers = snap.answers && typeof snap.answers === 'object' ? snap.answers : {};
  favs = snap.favs && typeof snap.favs === 'object' ? snap.favs : {};
  localAt = Number(snap.updatedAt || 0) || 0;
  saveLocalOnly();
  if(typeof list !== 'undefined'){
    list = buildList();
    if(pos > list.length - 1) pos = Math.max(0, list.length - 1);
    render(); buildTabs();
  }
}

function pullRemote(){
  return fetch(API + '?t=' + Date.now(), { cache: 'no-store' })
    .then(r => { if(!r.ok) throw 0; return r.json(); })
    .then(snap => {
      synced = true;
      const remoteAt = Number(snap.updatedAt || 0) || 0;
      if(remoteAt > localAt + 500){
        adopt(snap);
        setSync('ok', '已同步');
      } else {
        setSync('ok', '已同步 ' + new Date().toLocaleTimeString('zh-CN', {hour12:false}));
        if(localAt > remoteAt) schedulePush();
      }
    })
    .catch(() => { synced = false; setSync('off', '未连服务器'); });
}

let pid = PAPERS.length ? PAPERS[PAPERS.length - 1].id : '';
let filter = 'all';
let list = [];
let pos = 0;
let favTab = null;

const key = q => q.pid + ':' + q.n;
const paperById = id => PAPERS.find(p => p.id === id);
const curPaper = () => paperById(pid);

function buildList(){
  if(filter === 'fav'){
    const out = [];
    PAPERS.forEach(p => p.questions.forEach(q => {
      if(favs[p.id + ':' + q.n]) out.push(Object.assign({}, q, {pid: p.id, date: p.date, issue: p.issue}));
    }));
    return out;
  }
  const p = curPaper();
  if(!p) return [];
  let qs = p.questions;
  if(filter !== 'all') qs = qs.filter(q => q.sec === filter);
  return qs.map(q => Object.assign({}, q, {pid: p.id, date: p.date, issue: p.issue}));
}

function statsAll(){
  let total = 0, done = 0, right = 0;
  PAPERS.forEach(p => p.questions.forEach(q => {
    total++;
    const a = answers[p.id + ':' + q.n];
    if(a){ done++; if(a === q.ans) right++; }
  }));
  return {total, done, right, rate: done ? Math.round(right/done*100) : null};
}

function statsPaper(){
  const p = curPaper();
  if(!p) return {total:0, done:0};
  let done = 0;
  p.questions.forEach(q => { if(answers[p.id + ':' + q.n]) done++; });
  return {total: p.questions.length, done};
}

function refreshHeader(){
  const s = statsAll();
  $('#totalN').textContent = s.total;
  $('#doneN').textContent = s.done;
  const r = $('#rate');
  if(s.rate === null){ r.textContent = '—'; r.style.color = '#9ca3af'; }
  else {
    r.textContent = s.rate + '%';
    r.style.color = s.rate >= 80 ? '#15803d' : (s.rate >= 60 ? '#b45309' : '#b91c1c');
  }
  const nf = Object.keys(favs).length;
  $('#favN').textContent = '★ ' + nf;
  if(favTab) favTab.textContent = '★ 收藏 ' + nf;
  const sp = statsPaper();
  const p = curPaper();
  if(filter === 'fav'){
    const cur = list.length ? ('　当前 ' + (pos + 1) + '/' + list.length) : '';
    $('#sub').textContent = '收藏夹 · 跨 ' + PAPERS.length + ' 期汇总　共 ' + nf + ' 题' + cur;
  } else {
    $('#sub').textContent = p ? ('第 ' + p.issue + ' 期 · ' + p.date + '　本页 ' + sp.done + '/' + sp.total) : '';
  }
  $('#pbar').style.width = (s.done / (s.total || 1) * 100).toFixed(1) + '%';
}

function buildDates(){
  const box = $('#dates');
  box.innerHTML = '';
  PAPERS.forEach(p => {
    const b = document.createElement('button');
    b.className = 'date' + (p.id === pid ? ' on' : '');
    b.innerHTML = '<b>' + p.date.slice(5) + '</b><small>' + p.issue + '</small>';
    b.onclick = () => {
      pid = p.id; filter = 'all'; pos = 0;
      list = buildList();
      buildDates(); buildTabs(); render();
    };
    box.appendChild(b);
  });
}

function buildTabs(){
  const box = $('#tabs');
  box.innerHTML = '';
  const all = document.createElement('button');
  all.className = 'tab' + (filter === 'all' ? ' on' : '');
  all.textContent = '全部 ' + (curPaper() ? curPaper().questions.length : 0);
  all.onclick = () => { filter = 'all'; list = buildList(); pos = 0; render(); buildTabs(); };
  box.appendChild(all);

  favTab = document.createElement('button');
  favTab.className = 'tab' + (filter === 'fav' ? ' on' : '');
  favTab.textContent = '★ 收藏 ' + Object.keys(favs).length;
  favTab.onclick = () => { filter = 'fav'; list = buildList(); pos = 0; render(); buildTabs(); };
  box.appendChild(favTab);

  const p = curPaper();
  if(p) p.sections.forEach(sec => {
    const b = document.createElement('button');
    b.className = 'tab' + (filter === sec.name ? ' on' : '');
    b.textContent = sec.short;
    b.onclick = () => { filter = sec.name; list = buildList(); pos = 0; render(); buildTabs(); };
    box.appendChild(b);
  });
}

function renderEmpty(){
  $('#qno').textContent = '—';
  $('#qsec').textContent = '暂无题目';
  $('#qfrom').style.display = 'none';
  $('#qtext').textContent = '这里还没有题目。点题卡右上角的 ☆ 可以把想反复看的题收藏起来，之后在这里集中复习，各期收藏会汇总在一起。';
  $('#opts').innerHTML = '';
  $('#exp').classList.remove('show');
  $('#star').style.visibility = 'hidden';
  $('#prev').disabled = true;
  $('#next').disabled = true;
  refreshHeader();
  buildGrid();
}

function render(){
  if(!list.length){ renderEmpty(); return; }
  const q = list[pos];
  const sel = answers[key(q)];

  const st = $('#star');
  st.style.visibility = 'visible';
  const isFav = !!favs[key(q)];
  st.textContent = isFav ? '★' : '☆';
  st.classList.toggle('on', isFav);
  st.onclick = () => {
    if(favs[key(q)]) delete favs[key(q)]; else favs[key(q)] = 1;
    saveAll();
    if(filter === 'fav'){
      list = buildList();
      if(pos > list.length - 1) pos = Math.max(0, list.length - 1);
    }
    render(); buildTabs();
  };

  $('#qno').textContent = '第 ' + q.n + ' 题';
  $('#qsec').textContent = q.sec;
  const fr = $('#qfrom');
  if(q.pid !== pid){ fr.style.display = ''; fr.textContent = '第 ' + q.issue + ' 期 · ' + q.date.slice(5); }
  else { fr.style.display = 'none'; }

  $('#qtext').textContent = q.q;

  const box = $('#opts');
  box.innerHTML = '';
  const letters = ['A','B','C','D'];
  q.opts.forEach((text, i) => {
    const k = letters[i];
    const b = document.createElement('button');
    b.className = 'opt';
    b.innerHTML = '<span class="k">' + k + '</span><span class="t"></span>';
    b.querySelector('.t').textContent = text;
    if(sel){
      b.classList.add('done');
      if(k === q.ans) b.classList.add('correct');
      else if(k === sel) b.classList.add('wrong');
      else b.classList.add('dim');
    } else {
      b.onclick = () => choose(k);
    }
    box.appendChild(b);
  });

  const exp = $('#exp');
  if(sel){
    exp.classList.add('show');
    const ok = sel === q.ans;
    const v = $('#verdict');
    v.className = 'verdict ' + (ok ? 'ok' : 'bad');
    v.innerHTML = (ok ? '✓ 回答正确' : '✗ 回答错误') + '<span class="badge">正确答案 ' + q.ans + '</span>';
    $('#tag').textContent = q.tag || '—';
    $('#expl').textContent = q.exp || '';
  } else {
    exp.classList.remove('show');
  }

  $('#redo').onclick = () => { delete answers[key(q)]; saveAll(); render(); };

  $('#prev').disabled = pos === 0;
  $('#next').disabled = pos === list.length - 1;
  $('#sheetBtn').textContent = '答题卡 ' + list.length;
  refreshHeader();
  buildGrid();
  window.scrollTo({top:0, behavior:'smooth'});
}

function choose(k){
  const q = list[pos];
  if(answers[key(q)]) return;
  answers[key(q)] = k;
  saveAll();
  render();
}

function go(d){
  const np = pos + d;
  if(np < 0 || np >= list.length) return;
  pos = np; render();
}

function buildGrid(){
  const g = $('#grid');
  g.innerHTML = '';
  const cur = list[pos] ? key(list[pos]) : '';
  $('#sheetTitle').textContent = (filter === 'fav' ? '答题卡 · 全部收藏' : '答题卡 · 第 ' + (curPaper() ? curPaper().issue : '') + ' 期');
  list.forEach(q => {
    const c = document.createElement('div');
    c.className = 'cell';
    c.textContent = q.n;
    const a = answers[key(q)];
    if(a) c.classList.add(a === q.ans ? 'ok' : 'bad');
    if(favs[key(q)]) c.classList.add('fav');
    if(key(q) === cur) c.classList.add('cur');
    c.onclick = () => { pos = list.findIndex(x => key(x) === key(q)); render(); closeSheet(); };
    g.appendChild(c);
  });
}

function openSheet(){ $('#mask').classList.add('show'); document.body.style.overflow='hidden'; buildGrid(); }
function closeSheet(){ $('#mask').classList.remove('show'); document.body.style.overflow=''; }

$('#prev').onclick = () => go(-1);
$('#next').onclick = () => go(1);
$('#sheetBtn').onclick = openSheet;
$('#closeSheet').onclick = closeSheet;
$('#closeTop').onclick = closeSheet;
$('#mask').onclick = e => { if(e.target === $('#mask')) closeSheet(); };

$('#jumpWrong').onclick = () => {
  const after = list.findIndex((q, i) => i > pos && answers[key(q)] && answers[key(q)] !== q.ans);
  if(after >= 0){ pos = after; render(); closeSheet(); return; }
  const any = list.findIndex(q => answers[key(q)] && answers[key(q)] !== q.ans);
  if(any >= 0){ pos = any; render(); closeSheet(); }
  else alert('当前范围内没有错题。');
};

$('#resetAll').onclick = () => {
  const label = filter === 'fav' ? '收藏夹' : ('第 ' + (curPaper() ? curPaper().issue : '') + ' 期');
  if(confirm('清空' + label + '的答题记录？（收藏不受影响）')){
    list.forEach(q => { delete answers[key(q)]; });
    saveAll(); pos = 0; render();
  }
};

document.addEventListener('keydown', e => {
  const k = e.key.toUpperCase();
  if(['1','2','3','4'].includes(k)) choose(['A','B','C','D'][+k - 1]);
  else if(['A','B','C','D'].includes(k)) choose(k);
  else if(k === 'F'){ const b = $('#star'); if(b && b.style.visibility !== 'hidden') b.click(); }
  else if(e.key === 'ArrowLeft') go(-1);
  else if(e.key === 'ArrowRight') go(1);
  else if(e.key === 'Escape') closeSheet();
});

function showWarn(html){
  const w = $('#warnbar');
  if(!w) return;
  w.innerHTML = html;
  w.style.display = 'block';
}

$('#expBtn').onclick = () => {
  const pad = n => String(n).padStart(2, '0');
  const d = new Date();
  const data = { app: 'gdquiz', v: 2, exportedAt: d.toISOString(), answers, favs };
  const blob = new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '广东省考刷题_记录_' + d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate()) + '.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1500);
};

$('#impBtn').onclick = () => $('#impFile').click();

$('#impFile').onchange = e => {
  const f = e.target.files && e.target.files[0];
  if(!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    try{
      const o = JSON.parse(rd.result);
      if(!o || typeof o !== 'object' || (!o.answers && !o.favs)) throw 0;
      let na = 0, nf = 0;
      Object.keys(o.answers || {}).forEach(k => { if(!answers[k] && o.answers[k]){ answers[k] = o.answers[k]; na++; } });
      Object.keys(o.favs || {}).forEach(k => { if(!favs[k] && o.favs[k]){ favs[k] = 1; nf++; } });
      saveAll();
      list = buildList();
      if(pos > list.length - 1) pos = 0;
      render(); buildTabs(); closeSheet();
      alert('已恢复：新增作答 ' + na + ' 题、收藏 ' + nf + ' 题。原有记录未被覆盖。');
    }catch(err){
      alert('这个文件读不出来。请选择本页「备份记录」导出的 json 文件。');
    }
    e.target.value = '';
  };
  rd.readAsText(f);
};

$('#sub').textContent = QUIZ.meta.label;
buildDates();
buildTabs();
list = buildList();
render();

pullRemote();
document.addEventListener('visibilitychange', () => { if(!document.hidden) pullRemote(); });
window.addEventListener('focus', () => pullRemote());

if(!STORE_OK){
  showWarn('<b>本页存不下记录</b>　当前打开方式禁用了浏览器本地存储，答过的题和收藏一刷新就没了。两个办法：① 把 <b>广东省考刷题.html</b> 下载到电脑，双击用浏览器打开再刷（同目录下记录会一直留着）；② 在这里刷完点答题卡里的「备份记录」，换地方后再「恢复记录」。');
}
</script>
</body>
</html>
"""


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "广东省考刷题.html"

    papers = []
    for md in sorted(HERE.glob("*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})_第(\d+)期", md.stem)
        if not m:
            continue
        date_s, issue = m.group(1), m.group(2)
        qs = parse(md.read_text(encoding="utf-8"))
        papers.append({
            "id": f"{date_s}-{issue}",
            "date": date_s,
            "issue": issue,
            "label": f"第 {issue} 期 · {date_s}",
            "sections": build_sections(qs),
            "questions": qs,
        })

    papers.sort(key=lambda p: (p["date"], p["issue"]))
    if not papers:
        raise SystemExit("题库目录里没有找到形如 2026-11-16_第003期_*.md 的文件")

    total = sum(len(p["questions"]) for p in papers)
    data = {
        "meta": {"label": f"共 {len(papers)} 期 · {total} 题"},
        "papers": papers,
    }

    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__TITLE__", "广东省考刷题总入口"))

    out.write_text(html, encoding="utf-8")
    print(f"OK  {len(papers)} 期 / {total} 题 -> {out}")
    for p in papers:
        print(f"    {p['date']}  第{p['issue']}期  {len(p['questions'])} 题  小节 {len(p['sections'])}")


if __name__ == "__main__":
    main()
