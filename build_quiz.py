#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把每日刷题的 Markdown 题库转换为可点击作答的交互式 HTML。

用法：
    python build_quiz.py <题库.md> [输出.html]

约定（与自动化生成的题库保持一致）：
    题干   **12.** 题干文字（　）。
    选项   A. 选项文字      （B/C/D 同）
    答案   **12. C**　考点：xxx｜一句话解析
小节标题 ### 一、广东省情与粤港澳大湾区（1—20）
"""
import json
import re
import sys
import pathlib

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

/* ---------- 顶栏 ---------- */
header{
  position:sticky;top:0;z-index:30;background:rgba(244,245,247,.92);
  backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line);
}
.htop{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 0 10px}
.brand{font-size:16px;font-weight:650;letter-spacing:.2px}
.brand small{display:block;font-weight:400;font-size:12px;color:var(--sub);margin-top:2px;letter-spacing:0}
.hstat{text-align:right;font-size:12px;color:var(--sub);white-space:nowrap}
.hstat b{font-size:19px;color:var(--ink);font-variant-numeric:tabular-nums}
.hstat .rate{font-weight:600;font-variant-numeric:tabular-nums}
.pbar{height:3px;background:#e3e5ea;border-radius:0 0 3px 3px;overflow:hidden}
.pbar i{display:block;height:100%;width:0;background:var(--primary);transition:width .35s ease}

/* ---------- 分组 ---------- */
.tabs{display:flex;gap:8px;overflow-x:auto;padding:12px 0 14px;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{
  flex:0 0 auto;border:1px solid var(--line);background:#fff;color:#4b5563;
  padding:6px 13px;border-radius:999px;font-size:13px;cursor:pointer;white-space:nowrap;
  transition:.15s;
}
.tab:hover{border-color:#c9ced8}
.tab.on{background:var(--ink);border-color:var(--ink);color:#fff}

/* ---------- 题目卡 ---------- */
.qcard{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:22px 22px 18px}
.qmeta{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--sub);margin-bottom:12px}
.qmeta .no{font-weight:600;color:var(--primary);background:var(--primary-soft);padding:2px 9px;border-radius:6px;font-variant-numeric:tabular-nums}
.qmeta .sec{padding:2px 9px;background:#f3f4f6;border-radius:6px}
.star{
  margin-left:auto;background:none;border:0;padding:2px 6px;border-radius:7px;
  font-size:19px;line-height:1;color:#c3c8d2;cursor:pointer;transition:.15s;
  font-family:inherit;
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

/* ---------- 解析 ---------- */
.exp{margin-top:18px;border-top:1px dashed var(--line);padding-top:16px;display:none}
.exp.show{display:block;animation:fade .22s ease}
@keyframes fade{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.verdict{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600;margin-bottom:10px;padding:6px 11px;border-radius:8px;width:fit-content}
.verdict.ok{color:#166534;background:#dcfce7}
.verdict.bad{color:#b91c1c;background:#fee2e2}
.verdict .badge{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px;background:rgba(255,255,255,.75);color:#4b5563}
.expline{display:flex;gap:8px;align-items:flex-start;margin-bottom:6px}
.expline .lbl{
  flex:0 0 auto;font-size:11.5px;font-weight:600;color:#6b7280;background:#f3f4f6;
  padding:2px 7px;border-radius:5px;margin-top:2px;
}
.expline .val{font-size:14.5px;line-height:1.8;color:#111827}
.redo{margin-top:14px;font-size:12.5px;color:#4b5563;background:#f3f4f6;border:0;border-radius:7px;padding:6px 12px;cursor:pointer;font-family:inherit}
.redo:hover{background:#e9ebef}

/* ---------- 底部操作 ---------- */
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
.btn.icon{padding:10px 13px}

/* ---------- 答题卡 ---------- */
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

<header>
  <div class="wrap">
    <div class="htop">
      <div class="brand">广东省考每日刷题<small id="sub"></small></div>
      <div class="hstat">
        <div><b id="doneN">0</b> / <span id="totalN">0</span> 已答</div>
        <div>正确率 <span class="rate" id="rate">—</span></div>
      </div>
    </div>
  </div>
  <div class="pbar"><i id="pbar"></i></div>
</header>

<div class="wrap">
  <div class="tabs" id="tabs"></div>

  <main class="qcard">
    <div class="qmeta">
      <span class="no" id="qno">第 1 题</span>
      <span class="sec" id="qsec"></span>
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

  <p class="hint">键盘 1—4 或 A—D 选择，← → 翻页，F 键收藏</p>
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
    <div class="sheethead"><h3>答题卡</h3><span class="close" id="closeTop">关闭</span></div>
    <div class="legend">
      <span><i style="background:#f0fdf4;border:1px solid #86efac"></i>答对</span>
      <span><i style="background:#fef2f2;border:1px solid #fca5a5"></i>答错</span>
      <span><i style="background:#fbfbfc;border:1px solid #e6e8ec"></i>未答</span>
      <span><b style="color:#f59e0b">★</b> 已收藏</span>
    </div>
    <div class="grid" id="grid"></div>
    <div class="sheetbar">
      <button class="btn" id="jumpWrong">跳到下一道错题</button>
      <button class="btn" id="resetAll">清空记录</button>
      <button class="btn" id="closeSheet">关闭</button>
    </div>
  </div>
</div>

<script>
const QUIZ = __DATA__;

const KEY = 'gdquiz-' + QUIZ.meta.id;
const $ = s => document.querySelector(s);

const FKEY = KEY + '-fav';

let answers = {};
try { answers = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ answers = {}; }

let favs = {};
try { favs = JSON.parse(localStorage.getItem(FKEY) || '{}'); } catch(e){ favs = {}; }

let list = QUIZ.questions.slice();   // 当前筛选后的题序
let pos = 0;                          // 在 list 中的位置
let filter = 'all';                   // all / 小节名 / fav
let favTab = null;

function save(){ try{ localStorage.setItem(KEY, JSON.stringify(answers)); }catch(e){} }
function saveFav(){ try{ localStorage.setItem(FKEY, JSON.stringify(favs)); }catch(e){} }

function stats(){
  const total = QUIZ.questions.length;
  let done = 0, right = 0;
  QUIZ.questions.forEach(q => {
    const a = answers[q.n];
    if(a){ done++; if(a === q.ans) right++; }
  });
  return {total, done, right, rate: done ? Math.round(right/done*100) : null};
}

function refreshHeader(){
  const s = stats();
  $('#totalN').textContent = s.total;
  $('#doneN').textContent = s.done;
  const r = $('#rate');
  if(s.rate === null){ r.textContent = '—'; r.style.color = '#9ca3af'; }
  else {
    r.textContent = s.rate + '%';
    r.style.color = s.rate >= 80 ? '#15803d' : (s.rate >= 60 ? '#b45309' : '#b91c1c');
  }
  $('#pbar').style.width = (s.done / s.total * 100).toFixed(1) + '%';
  if(favTab){ favTab.textContent = '★ 收藏 ' + Object.keys(favs).length; }
}

function buildTabs(){
  const box = $('#tabs');
  const all = document.createElement('button');
  all.className = 'tab on'; all.textContent = '全部 ' + QUIZ.questions.length;
  all.onclick = () => { filter = 'all'; list = QUIZ.questions.slice(); pos = 0; render(); markTab(all); };
  box.appendChild(all);

  favTab = document.createElement('button');
  favTab.className = 'tab';
  favTab.textContent = '★ 收藏 ' + Object.keys(favs).length;
  favTab.onclick = () => {
    filter = 'fav';
    list = QUIZ.questions.filter(q => favs[q.n]);
    pos = 0; render(); markTab(favTab);
  };
  box.appendChild(favTab);

  QUIZ.sections.forEach(sec => {
    const b = document.createElement('button');
    b.className = 'tab';
    b.textContent = sec.short;
    b.onclick = () => {
      filter = sec.name;
      list = QUIZ.questions.filter(q => q.sec === sec.name);
      pos = 0; render(); markTab(b);
    };
    box.appendChild(b);
  });
}
function markTab(el){
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t === el));
}

function renderEmpty(){
  $('#qno').textContent = '—';
  $('#qsec').textContent = '暂无题目';
  $('#qtext').textContent = '这里还没有题目。点题卡右上角的 ☆ 可以把想反复看的题收藏起来，之后在这里集中复习。';
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
  const sel = answers[q.n];

  const st = $('#star');
  st.style.visibility = 'visible';
  const isFav = !!favs[q.n];
  st.textContent = isFav ? '★' : '☆';
  st.classList.toggle('on', isFav);
  st.onclick = () => {
    if(favs[q.n]) delete favs[q.n]; else favs[q.n] = 1;
    saveFav();
    if(filter === 'fav'){
      list = QUIZ.questions.filter(x => favs[x.n]);
      if(pos > list.length - 1) pos = Math.max(0, list.length - 1);
    }
    render();
  };

  $('#qno').textContent = '第 ' + q.n + ' 题';
  $('#qsec').textContent = q.sec;
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
    v.innerHTML = (ok ? '✓ 回答正确' : '✗ 回答错误')
      + '<span class="badge">正确答案 ' + q.ans + '</span>';
    $('#tag').textContent = q.tag || '—';
    $('#expl').textContent = q.exp || '';
  } else {
    exp.classList.remove('show');
  }

  $('#redo').onclick = () => { delete answers[q.n]; save(); render(); };

  $('#prev').disabled = pos === 0;
  $('#next').disabled = pos === list.length - 1;
  $('#sheetBtn').textContent = '答题卡 ' + stats().done + '/' + stats().total;
  refreshHeader();
  buildGrid();
  window.scrollTo({top:0, behavior:'smooth'});
}

function choose(k){
  const q = list[pos];
  if(answers[q.n]) return;
  answers[q.n] = k;
  save();
  render();
}

function go(d){
  const np = pos + d;
  if(np < 0 || np >= list.length) return;
  pos = np; render();
}

function buildGrid(){
  const g = $('#grid');
  if(!g.dataset.built){
    g.dataset.built = '1';
  }
  g.innerHTML = '';
  const cur = list[pos] ? list[pos].n : -1;
  list.forEach(q => {
    const c = document.createElement('div');
    c.className = 'cell';
    c.textContent = q.n;
    const a = answers[q.n];
    if(a) c.classList.add(a === q.ans ? 'ok' : 'bad');
    if(favs[q.n]) c.classList.add('fav');
    if(q.n === cur) c.classList.add('cur');
    c.onclick = () => { pos = list.findIndex(x => x.n === q.n); render(); closeSheet(); };
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
  const wrongIdx = list.findIndex((q, i) => i > pos && answers[q.n] && answers[q.n] !== q.ans);
  if(wrongIdx >= 0){ pos = wrongIdx; render(); closeSheet(); }
  else {
    const any = list.findIndex(q => answers[q.n] && answers[q.n] !== q.ans);
    if(any >= 0){ pos = any; render(); closeSheet(); }
    else alert('当前范围内没有错题。');
  }
};

$('#resetAll').onclick = () => {
  if(confirm('清空本期的全部答题记录？')){
    answers = {}; save(); pos = 0; render();
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

$('#sub').textContent = QUIZ.meta.label;
buildTabs();
render();
</script>
</body>
</html>
"""


def parse(md: str):
    ans_pos = md.find("## 第三部分")
    if ans_pos < 0:
        raise SystemExit("未找到「## 第三部分　答案与解析」")
    qpart, apart = md[:ans_pos], md[ans_pos:]

    questions = {}
    order = []
    part, sec = "", ""
    cur = None

    for raw in qpart.splitlines():
        s = raw.strip()
        if s.startswith("## "):
            if "常识判断" in s:
                part = "常识判断"
            elif "政治理论" in s:
                part = "政治理论"
            continue
        m = re.match(r"^###\s*(?:[一二三四五六七八九十]+、)?(.+?)（\d+—\d+）\s*$", s)
        if m:
            sec = m.group(1).strip()
            continue
        m = re.match(r"^\*\*(\d+)\.\*\*\s*(.+)$", s)
        if m:
            n = int(m.group(1))
            cur = {"n": n, "part": part, "sec": sec, "q": m.group(2).strip(), "opts": []}
            questions[n] = cur
            order.append(n)
            continue
        m = re.match(r"^([A-D])\.\s*(.+)$", s)
        if m and cur is not None and len(cur["opts"]) < 4:
            cur["opts"].append(m.group(2).strip())
            continue

    answers = {}
    for raw in apart.splitlines():
        s = raw.strip()
        m = re.match(r"^\*\*(\d+)\.\s*([A-D])\*\*\s*(.*)$", s)
        if not m:
            continue
        n, letter, rest = int(m.group(1)), m.group(2), m.group(3)
        rest = rest.replace("　", " ").strip()
        tag, exp = "", rest
        mt = re.search(r"考点：(.+?)[｜|](.*)$", rest)
        if mt:
            tag = mt.group(1).strip()
            exp = mt.group(2).strip()
        answers[n] = (letter, tag, exp)

    out = []
    for n in order:
        q = questions[n]
        if len(q["opts"]) != 4:
            raise SystemExit(f"第 {n} 题选项数量异常：{len(q['opts'])}")
        if n not in answers:
            raise SystemExit(f"第 {n} 题缺少答案")
        letter, tag, exp = answers[n]
        out.append({
            "n": n, "part": q["part"], "sec": q["sec"],
            "q": cn_quotes(q["q"]),
            "opts": [cn_quotes(o) for o in q["opts"]],
            "ans": letter, "tag": cn_quotes(tag), "exp": cn_quotes(exp),
        })
    return out


def cn_quotes(s: str) -> str:
    """把成对的英文直引号换成中文引号；引号数为奇数时原样返回，避免错位。"""
    if s.count('"') % 2 != 0:
        return s
    out, opening = [], True
    for ch in s:
        if ch == '"':
            out.append('“' if opening else '”')
            opening = not opening
        else:
            out.append(ch)
    return ''.join(out)


def build_sections(qs):
    secs, seen = [], {}
    for q in qs:
        key = (q["part"], q["sec"])
        if key not in seen:
            seen[key] = {"part": q["part"], "name": q["sec"], "short": q["part"][:2] + "·" + q["sec"], "items": []}
            secs.append(seen[key])
        seen[key]["items"].append(q["n"])
    result = []
    for s in secs:
        result.append({
            "part": s["part"],
            "name": s["name"],
            "short": s["name"] if len(s["name"]) <= 12 else s["name"][:11] + "…",
        })
    return result


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法：python build_quiz.py <题库.md> [输出.html]")
    src = pathlib.Path(sys.argv[1])
    md = src.read_text(encoding="utf-8")
    qs = parse(md)

    m = re.search(r"(\d{4}-\d{2}-\d{2})_第(\d+)期", src.stem)
    date_s = m.group(1) if m else ""
    issue = m.group(2) if m else "001"
    label = f"第 {issue} 期 · {date_s}　共 {len(qs)} 题"

    data = {
        "meta": {"id": f"{date_s}-{issue}", "label": label, "date": date_s, "issue": issue},
        "sections": build_sections(qs),
        "questions": qs,
    }

    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__TITLE__", f"广东省考刷题 第{issue}期 · {date_s}"))

    dst = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".html")
    dst.write_text(html, encoding="utf-8")
    print(f"OK  {len(qs)} 题 -> {dst}")
    print("    选项数分布:", {len(q['opts']) for q in qs})
    print("    答案分布:", {L: sum(1 for q in qs if q['ans'] == L) for L in 'ABCD'})
    print("    解析为空:", sum(1 for q in qs if not q['exp']))


if __name__ == "__main__":
    main()
