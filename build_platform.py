#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「每日刷题」与「成语速记」合成一个应用：省考平台.html（首页=平台总览）"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "省考平台.html"
SITE = HERE / "_site"
PAGES = HERE / "docs"

sys.path.insert(0, str(HERE))
from build_quiz import build_sections, parse  # noqa: E402
from build_vocab import clean_items  # noqa: E402


def load_quiz() -> dict:
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
    total = sum(len(p["questions"]) for p in papers)
    return {"meta": {"label": f"共 {len(papers)} 期 · {total} 题"}, "papers": papers}


def load_vocab() -> list[dict]:
    src = HERE / "_vocab" / "items.json"
    if not src.exists():
        return []
    return clean_items(json.loads(src.read_text(encoding="utf-8")))


def load_know() -> list[dict]:
    """知识点：知识点.json → 扁平卡片列表，每张带所属分类中文名。"""
    src = HERE / "知识点.json"
    if not src.exists():
        return []
    doc = json.loads(src.read_text(encoding="utf-8"))
    out = []
    for cat in doc.get("cats", []):
        for card in cat.get("cards", []):
            out.append({
                "id": card["id"],
                "cat": cat["id"],
                "cname": cat["name"],
                "t": card["t"],
                "tag": card.get("tag", ""),
                "items": card.get("items", []),
                "note": card.get("note", ""),
                "src": card.get("src", ""),
            })
    return out


def load_math() -> list[dict]:
    """数量关系：数量关系.json → 题目列表（工程问题 + 集合容斥）。"""
    src = HERE / "数量关系.json"
    if not src.exists():
        return []
    doc = json.loads(src.read_text(encoding="utf-8"))
    return doc.get("items", [])


def load_yanyu() -> list[dict]:
    """言语理解：言语理解.json → 题目列表（选词填空 / 片段阅读 / 语句表达）。"""
    src = HERE / "言语理解.json"
    if not src.exists():
        return []
    doc = json.loads(src.read_text(encoding="utf-8"))
    return doc.get("items", [])


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>广东省考学习平台</title>
<style>
:root{
  --ink:#111827; --sub:#6b7280; --line:#e6e8ec; --bg:#f5f6f8; --card:#fff;
  --gold:#f59e0b; --brown:#b45309;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-size:15px;line-height:1.7;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
button{font-family:inherit}
a{color:inherit}

/* ---------- 顶栏 ---------- */
header{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.95);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.wrap{max-width:820px;margin:0 auto;padding:0 16px}
.htop{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:13px 0 9px}
.brand{font-size:17px;font-weight:700;letter-spacing:.3px}
.brand small{display:block;font-size:11.5px;font-weight:400;color:var(--sub);margin-top:2px}
.hstat{text-align:right;font-size:11.5px;color:var(--sub);white-space:nowrap;line-height:1.6}
.hstat b{font-size:16px;color:var(--ink);font-variant-numeric:tabular-nums}
.hstat .fav{color:var(--brown)}
.sync{display:inline-block;margin-top:2px;font-size:10.5px;padding:1px 7px;border-radius:9px;
  border:1px solid var(--line);color:#9ca3af;background:#fafafa;cursor:pointer}
.sync.ok{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.sync.off{color:#b91c1c;border-color:#fecaca;background:#fef2f2}
.acct{display:inline-block;margin-top:2px;margin-left:4px;font-size:10.5px;padding:1px 8px;
  border-radius:9px;border:1px solid #c7d2fe;color:#4338ca;background:#eef2ff;cursor:pointer;font-weight:600}

nav{display:flex;gap:4px;padding-bottom:9px;overflow-x:auto;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav button{flex:0 0 auto;border:1px solid transparent;background:transparent;color:var(--sub);
  padding:6px 14px;border-radius:9px;font-size:13.5px;cursor:pointer;font-weight:500}
nav button.on{background:var(--ink);color:#fff;font-weight:600}

main{max-width:820px;margin:0 auto;padding:18px 16px 90px}

/* ---------- 首页 ---------- */
.hero{background:linear-gradient(135deg,#111827,#374151);color:#fff;border-radius:18px;
  padding:22px 22px 20px;margin-bottom:14px}
.hero h1{margin:0 0 4px;font-size:19px;font-weight:700;letter-spacing:.5px}
.hero p{margin:0;font-size:12.5px;color:#d1d5db}
.hero .row{display:flex;gap:22px;margin-top:16px;flex-wrap:wrap}
.hero .k{font-size:11px;color:#9ca3af}
.hero .v{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.hero .v small{font-size:12px;font-weight:400;color:#d1d5db}

.tiles{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.tile{background:#fff;border:1px solid var(--line);border-radius:15px;padding:16px 16px 14px;cursor:pointer;
  transition:transform .12s ease,box-shadow .12s ease}
.tile:hover{transform:translateY(-1px);box-shadow:0 6px 18px rgba(16,24,40,.07)}
.tile .t{font-size:13px;color:var(--sub);display:flex;align-items:center;gap:6px}
.tile .n{font-size:24px;font-weight:700;margin-top:6px;font-variant-numeric:tabular-nums}
.tile .n small{font-size:12px;font-weight:400;color:var(--sub)}
.tile .bar{height:5px;background:#eef0f3;border-radius:5px;margin-top:10px;overflow:hidden}
.tile .bar i{display:block;height:100%;background:var(--ink);border-radius:5px}
.tile .go{font-size:11.5px;color:var(--brown);margin-top:8px}

.sec-title{font-size:13px;font-weight:600;color:var(--sub);margin:18px 0 8px;letter-spacing:.3px}
.list{background:#fff;border:1px solid var(--line);border-radius:15px;overflow:hidden}
.prow{display:flex;align-items:center;gap:12px;padding:13px 16px;border-bottom:1px solid #f1f2f4;cursor:pointer}
.prow:last-child{border-bottom:0}
.prow:hover{background:#fafafa}
.prow .d{font-size:14.5px;font-weight:600}
.prow .i{font-size:11.5px;color:var(--sub)}
.prow .meta{margin-left:auto;font-size:11.5px;color:var(--sub);text-align:right}
.prow .dot{width:7px;height:7px;border-radius:50%;background:#e5e7eb;flex:0 0 auto}
.prow .dot.done{background:#15803d}
.prow .dot.part{background:var(--gold)}

/* ---------- 通用 ---------- */
.chips{display:flex;gap:6px;overflow-x:auto;padding:2px 0 12px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid var(--line);background:#fff;color:var(--sub);
  padding:5px 11px;border-radius:999px;font-size:12.5px;cursor:pointer;white-space:nowrap}
.chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.btn{padding:10px 14px;border-radius:11px;border:1px solid var(--line);background:#fff;
  font-size:14px;color:var(--ink);cursor:pointer}
.btn:disabled{color:#c7cbd1}
.btn.main{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
.empty{text-align:center;color:#9ca3af;font-size:13.5px;padding:56px 0}

/* ---------- 刷题 ---------- */
.dates{display:flex;gap:8px;overflow-x:auto;padding-bottom:10px;scrollbar-width:none}
.dates::-webkit-scrollbar{display:none}
.date{flex:0 0 auto;border:1px solid var(--line);background:#fff;border-radius:11px;
  padding:6px 12px;cursor:pointer;line-height:1.25;text-align:center;color:var(--ink)}
.date b{display:block;font-size:13.5px}
.date small{display:block;font-size:10.5px;color:var(--sub)}
.date.on{background:var(--ink);border-color:var(--ink);color:#fff}
.date.on small{color:#d1d5db}
.tabs{display:flex;gap:6px;overflow-x:auto;padding-bottom:12px;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:0 0 auto;border:1px solid var(--line);background:#fff;border-radius:999px;
  padding:5px 11px;font-size:12.5px;color:var(--sub);cursor:pointer;white-space:nowrap}
.tab.on{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}

.qcard{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 18px 16px;
  box-shadow:0 1px 2px rgba(16,24,40,.04);position:relative}
.qmeta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--sub);margin-bottom:12px}
.qmeta .no{font-weight:700;color:var(--ink);font-size:13px}
.qmeta .sec{background:#f3f4f6;border-radius:6px;padding:1px 8px}
.qmeta .from{background:#fffbeb;color:var(--brown);border:1px solid #fde68a;border-radius:6px;padding:1px 8px}
.star{position:absolute;top:13px;right:14px;width:38px;height:38px;border-radius:50%;border:0;
  background:transparent;font-size:21px;line-height:1;color:#d1d5db;cursor:pointer}
.star.on{color:var(--gold)}
.qtext{font-size:16.5px;line-height:1.85;font-weight:500;padding-right:34px}
.opts{margin-top:16px;display:flex;flex-direction:column;gap:9px}
.opt{display:flex;gap:10px;align-items:flex-start;text-align:left;width:100%;
  border:1px solid var(--line);background:#fff;border-radius:11px;padding:11px 13px;
  font-size:15px;line-height:1.6;color:var(--ink);cursor:pointer}
.opt:active{transform:scale(.995)}
.opt .k{flex:0 0 20px;font-weight:700;color:var(--sub)}
.opt.correct{border-color:#86efac;background:#f0fdf4}
.opt.correct .k{color:#15803d}
.opt.wrong{border-color:#fca5a5;background:#fef2f2}
.opt.wrong .k{color:#b91c1c}
.opt.dim{opacity:.62}
.opt.done{cursor:default}
.exp{display:none;margin-top:16px;border-top:1px dashed var(--line);padding-top:14px}
.exp.show{display:block}
.verdict{display:inline-block;font-size:12.5px;font-weight:600;border-radius:7px;padding:3px 9px;margin-bottom:10px}
.verdict.ok{background:#dcfce7;color:#15803d}
.verdict.bad{background:#fee2e2;color:#b91c1c}
.verdict .badge{background:rgba(255,255,255,.7);color:inherit;margin-left:8px;padding:0 6px;border-radius:5px}
.expline{display:flex;gap:8px;font-size:14px;line-height:1.85}
.expline .lbl{flex:0 0 32px;color:#9ca3af;font-size:12px;padding-top:2px}
.expline .val{color:#111827}
.qnav{display:flex;gap:10px;margin-top:14px}
.qnav .btn{flex:1;text-align:center}
.pos{text-align:center;font-size:12px;color:var(--sub);margin-top:10px}

.mask{position:fixed;inset:0;background:rgba(17,24,39,.45);display:none;z-index:60;
  align-items:flex-end;justify-content:center}
.mask.show{display:flex}
.sheet{background:#fff;width:100%;max-width:820px;border-radius:18px 18px 0 0;padding:0 18px 18px;
  max-height:82vh;overflow:auto}
.sheethead{position:sticky;top:0;background:#fff;display:flex;align-items:center;justify-content:space-between;
  padding:14px 0 10px;border-bottom:1px solid #f1f2f4;z-index:2}
.sheethead h3{margin:0;font-size:15px}
.close{font-size:13px;color:var(--sub);cursor:pointer}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--sub);padding:10px 0}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.grid{display:grid;grid-template-columns:repeat(10,1fr);gap:7px;padding:4px 0 6px}
.cell{aspect-ratio:1;display:flex;align-items:center;justify-content:center;border-radius:7px;
  border:1px solid var(--line);background:#fbfbfc;font-size:12px;cursor:pointer;position:relative;color:var(--sub)}
.cell.ok{background:#f0fdf4;border-color:#86efac;color:#15803d}
.cell.bad{background:#fef2f2;border-color:#fca5a5;color:#b91c1c}
.cell.fav::after{content:'★';position:absolute;top:0;right:2px;font-size:7.5px;color:var(--gold);line-height:1.4}
.cell.cur{outline:2px solid var(--ink);outline-offset:1px}
.sheetbar{display:flex;gap:8px;flex-wrap:wrap;position:sticky;bottom:0;background:#fff;padding:12px 0 2px;
  box-shadow:0 -10px 18px 6px #fff}
.sheetbar .btn{flex:1;text-align:center;font-size:13px}

/* ---------- 成语 ---------- */
.search{position:relative;margin-bottom:10px}
.search input{width:100%;padding:10px 13px;border:1px solid var(--line);border-radius:11px;
  font-size:14px;background:#fff;outline:none;font-family:inherit}
.search input:focus{border-color:#c7cdd6;box-shadow:0 0 0 3px #eef1f5}
.vtool{display:flex;gap:8px;align-items:center;margin-bottom:4px}
.seg{display:flex;background:#eceef2;border-radius:10px;padding:3px;gap:2px;flex:0 0 auto}
.seg button{border:0;background:transparent;padding:6px 12px;border-radius:8px;font-size:13px;color:var(--sub);cursor:pointer}
.seg button.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.06)}

.vcard{background:#fff;border:1px solid var(--line);border-radius:18px;padding:26px 22px 20px;
  min-height:240px;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;cursor:pointer;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.vcard .word{font-size:40px;font-weight:700;letter-spacing:6px;line-height:1.4;padding-left:6px}
.vcard .hintline{margin-top:16px;font-size:12.5px;color:#9ca3af}
.vcard .def{display:none;margin-top:16px;font-size:15.5px;line-height:1.95;color:#1f2937;
  text-align:left;width:100%;border-top:1px dashed var(--line);padding-top:16px}
.vcard.open .def{display:block}
.vcard.open .hintline{display:none}
.vcard .tagrow{display:flex;gap:6px;margin-top:14px;width:100%}
.vcard .tagrow span{font-size:11px;color:var(--sub);background:#f3f4f6;border-radius:6px;padding:2px 8px}
.vstar{position:absolute;top:12px;right:14px;width:38px;height:38px;border:0;background:transparent;
  font-size:22px;color:#d1d5db;cursor:pointer;line-height:1}
.vstar.on{color:var(--gold)}

.vlist{display:grid;gap:10px}
.vitem{background:#fff;border:1px solid var(--line);border-radius:13px;padding:13px 14px;position:relative;cursor:pointer}
.vitem .w{font-size:17px;font-weight:700;letter-spacing:1px;padding-right:26px}
.vitem .d{font-size:13.5px;line-height:1.85;color:#374151;margin-top:5px}
.vitem .k{position:absolute;top:9px;right:11px;font-size:16px;color:#d1d5db}
.vitem .k.on{color:var(--gold)}
.vitem.clip .d{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* ---------- 知识点 ---------- */
.tiles.three{grid-template-columns:repeat(3,1fr)}
.kcard{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 22px 18px;position:relative}
.kcard .kh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;padding-right:34px}
.kcard .kt{font-size:19px;font-weight:700;letter-spacing:.3px;line-height:1.55}
.kcard .kc{font-size:11px;color:var(--sub);background:#f3f4f6;border-radius:6px;padding:2px 8px;white-space:nowrap}
.ktag{font-size:11px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:1px 7px}
.kbar{height:1px;background:var(--line);margin:14px 0 2px}
.kitems{margin:0;padding:0;list-style:none;counter-reset:ki}
.kitems li{counter-increment:ki;position:relative;padding:7px 0 7px 30px;font-size:14.5px;
  line-height:1.8;color:#1f2937;border-bottom:1px dashed #f2f3f6}
.kitems li:last-child{border-bottom:0}
.kitems li::before{content:counter(ki);position:absolute;left:0;top:8px;width:19px;height:19px;
  border-radius:50%;background:#eef1f5;color:#4b5563;font-size:11px;font-weight:600;
  text-align:center;line-height:19px;font-variant-numeric:tabular-nums}
.knote{margin-top:12px;background:#fffbeb;border:1px solid #fde68a;border-radius:11px;
  padding:10px 12px;font-size:13px;line-height:1.85;color:#78350f}
.ksrc{margin-top:10px;font-size:11.5px;color:#9ca3af}
.kmask{display:none}
.kcard.hide .kitems,.kcard.hide .knote{display:none}
.kcard.hide .kmask{display:block;margin-top:16px;font-size:13.5px;color:#9ca3af;text-align:center;
  padding:34px 0;border:1px dashed var(--line);border-radius:12px}
.kitem{background:#fff;border:1px solid var(--line);border-radius:13px;padding:13px 14px 12px;position:relative}
.kitem .kt2{font-size:15.5px;font-weight:700;padding-right:26px;line-height:1.6}
.kitem .kc2{font-size:11px;color:var(--sub);margin-top:3px}
.kitem .kb{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.kitem .kb span{font-size:12px;color:#374151;background:#f6f7f9;border:1px solid #eef0f3;
  border-radius:7px;padding:2px 8px;line-height:1.6}
.kitem .k{position:absolute;top:9px;right:11px;font-size:16px;color:#d1d5db;cursor:pointer}
.kitem .k.on{color:var(--gold)}

/* ---------- 数量关系 ---------- */
.tiles.four{grid-template-columns:repeat(4,1fr)}
.tiles.five{grid-template-columns:repeat(5,1fr)}
.mhero{background:linear-gradient(135deg,#1f2937,#4b5563);color:#fff;border-radius:18px;
  padding:20px 22px 18px;margin-bottom:14px}
.mhero .mt{font-size:18px;font-weight:700;letter-spacing:.4px}
.mhero .ms{font-size:12.5px;color:#d1d5db;margin-top:5px;line-height:1.7}
.mhero .mrow{display:flex;gap:22px;margin-top:14px;flex-wrap:wrap}
.mhero .k{font-size:11px;color:#9ca3af}
.mhero .v{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}
.mhero .v small{font-size:12px;font-weight:400;color:#d1d5db}
.mbar{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;
  color:var(--sub);margin-bottom:8px;font-variant-numeric:tabular-nums}
.mbar b{color:var(--ink)}
.mdots{display:flex;gap:6px;flex-wrap:wrap;padding:2px 0 10px}
.mdots i{width:22px;height:22px;border-radius:7px;border:1px solid var(--line);background:#fff;
  font-size:11px;font-style:normal;color:#9ca3af;display:flex;align-items:center;
  justify-content:center;cursor:pointer;font-variant-numeric:tabular-nums}
.mdots i.cur{border-color:var(--ink);color:var(--ink);font-weight:700}
.mdots i.r{background:#f0fdf4;border-color:#86efac;color:#15803d}
.mdots i.w{background:#fef2f2;border-color:#fca5a5;color:#b91c1c}
.mscore{display:flex;gap:26px;margin-top:6px;flex-wrap:wrap}

.foot{max-width:820px;margin:0 auto;padding:0 16px 36px;text-align:center;font-size:11.5px;color:#9ca3af;line-height:1.8}

@media (max-width:560px){
  .tiles{grid-template-columns:1fr 1fr}
  .tiles.three{grid-template-columns:1fr}
  .tiles.four{grid-template-columns:1fr 1fr}
  .tiles.five{grid-template-columns:1fr 1fr}
  .grid{grid-template-columns:repeat(8,1fr)}
  .vcard .word{font-size:34px;letter-spacing:4px}
  .qtext{font-size:16px}
}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <div class="htop">
      <div class="brand">广东省考学习平台<small id="sub">总览</small></div>
      <div class="hstat">
        <div><b id="doneN">0</b> / <span id="totalN">0</span> 已答　正确率 <b id="rate">—</b></div>
        <div>★ 题 <b class="fav" id="favN">0</b>　词 <b class="fav" id="vfavN">0</b>　点 <b class="fav" id="kfavN">0</b>　数 <b class="fav" id="mfavN">0</b>　言 <b class="fav" id="yfavN">0</b></div>
        <span class="sync" id="sync">连接中…</span>
        <span class="acct" id="acctBtn" style="display:none">登录同步</span>
      </div>
    </div>
    <nav id="nav">
      <button data-go="home" class="on">总览</button>
      <button data-go="quiz">每日刷题</button>
      <button data-go="vocab">成语速记</button>
      <button data-go="know">知识点</button>
      <button data-go="math">数量关系</button>
      <button data-go="yanyu">言语理解</button>
    </nav>

<main>
  <!-- 首页 -->
  <section id="v-home">
    <div class="hero">
      <h1>今天该做的五件事</h1>
      <p id="heroSub">刷题保持手感，言语理解每天一组，成语补底子，知识点背死该背的，数量关系练速度</p>
      <div class="row">
        <div><div class="k">刷题进度</div><div class="v" id="hDone">0<small> / 0</small></div></div>
        <div><div class="k">正确率</div><div class="v" id="hRate">—</div></div>
        <div><div class="k">收藏</div><div class="v" id="hFav">0<small> 题</small></div></div>
        <div><div class="k">成语收藏</div><div class="v" id="hVocab">0<small> 条</small></div></div>
        <div><div class="k">知识点收藏</div><div class="v" id="hKnow">0<small> 条</small></div></div>
        <div><div class="k">言语收藏</div><div class="v" id="hYan">0<small> 道</small></div></div>
      </div>
    </div>

    <div class="tiles five">
      <div class="tile" data-go="quiz">
        <div class="t">每日刷题</div>
        <div class="n" id="tQuizDone">0<small> 题已答</small></div>
        <div class="bar"><i id="tQuizBar" style="width:0%"></i></div>
        <div class="go">继续做题 →</div>
      </div>
      <div class="tile" data-go="vocab">
        <div class="t">成语速记</div>
        <div class="n" id="tVocabFav">0<small> 条已收藏</small></div>
        <div class="bar"><i id="tVocabBar" style="width:0%"></i></div>
        <div class="go">开始记忆 →</div>
      </div>
      <div class="tile" data-go="know">
        <div class="t">知识点</div>
        <div class="n" id="tKnowFav">0<small> 条已收藏</small></div>
        <div class="bar"><i id="tKnowBar" style="width:0%"></i></div>
        <div class="go">背原则 →</div>
      </div>
      <div class="tile" data-go="math">
        <div class="t">数量关系</div>
        <div class="n" id="tMathDone">0<small> 道已做</small></div>
        <div class="bar"><i id="tMathBar" style="width:0%"></i></div>
        <div class="go">练一组 →</div>
      </div>
      <div class="tile" data-go="yanyu">
        <div class="t">言语理解</div>
        <div class="n" id="tYanDone">0<small> 道已做</small></div>
        <div class="bar"><i id="tYanBar" style="width:0%"></i></div>
        <div class="go">刷一组 →</div>
      </div>
    </div>

    <div class="sec-title">各期进度</div>
    <div class="list" id="paperList"></div>

    <div class="sec-title">最近收藏的成语</div>
    <div class="list" id="favPreview"></div>

    <div class="sec-title">最近收藏的知识点</div>
    <div class="list" id="kfavPreview"></div>
  </section>

  <!-- 刷题 -->
  <section id="v-quiz" style="display:none">
    <div class="dates" id="dates"></div>
    <div class="tabs" id="tabs"></div>
    <div class="qcard">
      <button class="star" id="star" title="收藏本题（F）">☆</button>
      <div class="qmeta">
        <span class="no" id="qno">第 1 题</span>
        <span class="sec" id="qsec"></span>
        <span class="from" id="qfrom" style="display:none"></span>
      </div>
      <div class="qtext" id="qtext"></div>
      <div class="opts" id="opts"></div>
      <div class="exp" id="exp">
        <div class="verdict" id="verdict"></div>
        <div class="expline"><span class="lbl">考点</span><span class="val" id="tag"></span></div>
        <div class="expline"><span class="lbl">解析</span><span class="val" id="expl"></span></div>
      </div>
    </div>
    <div class="qnav">
      <button class="btn" id="prev">上一题</button>
      <button class="btn" id="sheetBtn">答题卡</button>
      <button class="btn main" id="next">下一题</button>
    </div>
    <div class="pos" id="pos"></div>
  </section>

  <!-- 成语 -->
  <section id="v-vocab" style="display:none">
    <div class="search"><input id="vq" type="search" placeholder="搜成语或释义里的字…" autocomplete="off"></div>
    <div class="vtool">
      <div class="seg">
        <button id="vmCard" class="on">卡片</button>
        <button id="vmList">全览</button>
      </div>
    </div>
    <div class="chips" id="vchips"></div>

    <div id="vCardView">
      <div class="vcard" id="vcard">
        <button class="vstar" id="vstar" title="收藏（F）">☆</button>
        <div class="word" id="vword">—</div>
        <div class="hintline">点击卡片看释义　·　空格翻面</div>
        <div class="def" id="vdef"></div>
        <div class="tagrow" id="vtags"></div>
      </div>
      <div class="qnav">
        <button class="btn" id="vprev">上一个</button>
        <button class="btn main" id="vnext">下一个</button>
      </div>
      <div class="qnav">
        <button class="btn" id="vshuffle">随机一条</button>
        <button class="btn" id="vreveal">显示释义</button>
      </div>
      <div class="pos" id="vpos"></div>
    </div>

    <div id="vListView" style="display:none">
      <div class="vlist" id="vgrid"></div>
      <div class="empty" id="vempty" style="display:none">没有符合条件的成语</div>
    </div>
  </section>

  <!-- 知识点 -->
  <section id="v-know" style="display:none">
    <div class="search"><input id="kq" type="search" placeholder="搜知识点，如「六个坚持」「六大纪律」「千亿斤」…" autocomplete="off"></div>
    <div class="vtool">
      <div class="seg">
        <button id="kmCard" class="on">卡片</button>
        <button id="kmList">全览</button>
      </div>
      <div class="seg">
        <button id="khide">遮盖自测</button>
      </div>
    </div>
    <div class="chips" id="kchips"></div>

    <div id="kCardView">
      <div class="kcard" id="kcard">
        <button class="vstar" id="kstar" title="收藏（F）">☆</button>
        <div class="kh"><div class="kt" id="kt">—</div></div>
        <div class="kbar"></div>
        <ol class="kitems" id="kitems"></ol>
        <div class="kmask" id="kmask">点一下揭晓要点</div>
        <div class="knote" id="knote" style="display:none"></div>
        <div class="ksrc" id="ksrc"></div>
      </div>
      <div class="qnav">
        <button class="btn" id="kprev">上一条</button>
        <button class="btn main" id="knext">下一条</button>
      </div>
      <div class="qnav">
        <button class="btn" id="kshuffle">随机一条</button>
        <button class="btn" id="kreveal">显示／隐藏要点</button>
      </div>
      <div class="pos" id="kpos"></div>
    </div>

    <div id="kListView" style="display:none">
      <div class="vlist" id="kgrid"></div>
      <div class="empty" id="kempty" style="display:none">没有符合条件的知识点</div>
    </div>
  </section>

  <!-- 数量关系 -->
  <section id="v-math" style="display:none">
    <div id="mStart">
      <div class="mhero">
        <div class="mt">数量关系 · 一组 10 道</div>
        <div class="ms">工程问题与集合容斥两个题型，可以挑一个专项练，也可以混合抽题。<br>选完立刻判对错、看解析，交卷出成绩；题库优先出你没做过的题。</div>
        <div class="mrow">
          <div><div class="k">题库</div><div class="v"><span id="mPool">0</span><small> 道</small></div></div>
          <div><div class="k">已做过</div><div class="v"><span id="mDoneN">0</span><small> 道</small></div></div>
          <div><div class="k">正确率</div><div class="v" id="mRate">—</div></div>
          <div><div class="k">收藏</div><div class="v"><span id="mFavN">0</span><small> 道</small></div></div>
        </div>
        <div class="chips" id="mchips" style="margin-top:12px;padding-bottom:0"></div>
      </div>
      <div class="qnav">
        <button class="btn main" id="mStartBtn">开始一组（10 道）</button>
      </div>
      <div class="qnav">
        <button class="btn" id="mFavBtn">只练收藏的题</button>
        <button class="btn" id="mResetBtn">清空本模块记录</button>
      </div>
      <div class="sec-title">上一次的成绩</div>
      <div class="list" id="mLast"></div>
    </div>

    <div id="mRun" style="display:none">
      <div class="mbar">
        <span>第 <b id="mIdx">1</b> / <span id="mTot">10</span> 题</span>
        <span id="mTimer">00:00</span>
      </div>
      <div class="mdots" id="mdots"></div>
      <div class="qcard">
        <button class="star" id="mstar" title="收藏本题（F）">☆</button>
        <div class="qmeta">
          <span class="no" id="mno">第 1 题</span>
          <span class="sec" id="mtag"></span>
        </div>
        <div class="qtext" id="mqtext"></div>
        <div class="opts" id="mopts"></div>
        <div class="exp" id="mexp">
          <div class="verdict" id="mverdict"></div>
          <div class="expline"><span class="lbl">解析</span><span class="val" id="mexpl"></span></div>
        </div>
      </div>
      <div class="qnav">
        <button class="btn" id="mprev">上一题</button>
        <button class="btn main" id="mnext">下一题</button>
      </div>
      <div class="qnav">
        <button class="btn" id="mfinish">交卷看成绩</button>
        <button class="btn" id="mquit">退出本组</button>
      </div>
    </div>

    <div id="mDone" style="display:none">
      <div class="mhero">
        <div class="mt" id="mScoreT">—</div>
        <div class="ms" id="mScoreS"></div>
        <div class="mrow">
          <div><div class="k">正确</div><div class="v" id="mRight">0</div></div>
          <div><div class="k">错误</div><div class="v" id="mWrong">0</div></div>
          <div><div class="k">用时</div><div class="v" id="mUsed">—</div></div>
        </div>
      </div>
      <div class="sec-title">这一组的错题</div>
      <div class="list" id="mWrongList"></div>
      <div class="qnav">
        <button class="btn main" id="mAgain">再来一组</button>
        <button class="btn" id="mBack">回到开始页</button>
      </div>
    </div>
  </section>

  <!-- 言语理解 -->
  <section id="v-yanyu" style="display:none">
    <div id="yStart">
      <div class="mhero">
        <div class="mt">言语理解 · 一组 10 道</div>
        <div class="ms">选词填空、片段阅读、语句表达三类，可以挑一类专项练，也可以混合抽题。<br>选完立刻判对错、看解析，交卷出成绩；题库优先出你没做过的题。</div>
        <div class="mrow">
          <div><div class="k">题库</div><div class="v"><span id="yPool">0</span><small> 道</small></div></div>
          <div><div class="k">已做过</div><div class="v"><span id="yDoneN">0</span><small> 道</small></div></div>
          <div><div class="k">正确率</div><div class="v" id="yRate">—</div></div>
          <div><div class="k">收藏</div><div class="v"><span id="yFavN">0</span><small> 道</small></div></div>
        </div>
        <div class="chips" id="ychips" style="margin-top:12px;padding-bottom:0"></div>
      </div>
      <div class="qnav">
        <button class="btn main" id="yStartBtn">开始一组（10 道）</button>
      </div>
      <div class="qnav">
        <button class="btn" id="yFavBtn">只练收藏的题</button>
        <button class="btn" id="yResetBtn">清空本模块记录</button>
      </div>
      <div class="sec-title">上一次的成绩</div>
      <div class="list" id="yLast"></div>
    </div>

    <div id="yRun" style="display:none">
      <div class="mbar">
        <span>第 <b id="yIdx">1</b> / <span id="yTot">10</span> 题</span>
        <span id="yTimer">00:00</span>
      </div>
      <div class="mdots" id="ydots"></div>
      <div class="qcard">
        <button class="star" id="ystar" title="收藏本题（F）">☆</button>
        <div class="qmeta">
          <span class="no" id="yno">第 1 题</span>
          <span class="sec" id="ytag"></span>
        </div>
        <div class="qtext" id="yqtext"></div>
        <div class="opts" id="yopts"></div>
        <div class="exp" id="yexp">
          <div class="verdict" id="yverdict"></div>
          <div class="expline"><span class="lbl">解析</span><span class="val" id="yexpl"></span></div>
        </div>
      </div>
      <div class="qnav">
        <button class="btn" id="yprev">上一题</button>
        <button class="btn main" id="ynext">下一题</button>
      </div>
      <div class="qnav">
        <button class="btn" id="yfinish">交卷看成绩</button>
        <button class="btn" id="yquit">退出本组</button>
      </div>
    </div>

    <div id="yDone" style="display:none">
      <div class="mhero">
        <div class="mt" id="yScoreT">—</div>
        <div class="ms" id="yScoreS"></div>
        <div class="mrow">
          <div><div class="k">正确</div><div class="v" id="yRight">0</div></div>
          <div><div class="k">错误</div><div class="v" id="yWrong">0</div></div>
          <div><div class="k">用时</div><div class="v" id="yUsed">—</div></div>
        </div>
      </div>
      <div class="sec-title">这一组的错题</div>
      <div class="list" id="yWrongList"></div>
      <div class="qnav">
        <button class="btn main" id="yAgain">再来一组</button>
        <button class="btn" id="yBack">回到开始页</button>
      </div>
    </div>
  </section>
</main>

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
      <button class="btn" id="expBtn">备份</button>
      <button class="btn" id="impBtn">恢复</button>
      <button class="btn" id="resetAll">清空本页</button>
      <button class="btn" id="closeSheet">关闭</button>
      <input type="file" id="impFile" accept=".json,application/json" style="display:none">
    </div>
  </div>
</div>

<p class="foot">刷题题库按期编排，成语来自《高频800词记忆版》OCR 整理，知识点取自《时政考点库》《时政素材》与考纲常考条目，数量关系收工程问题 46 道、集合容斥 40 道，言语理解收选词填空 23 道、片段阅读 21 道、语句表达 16 道（每题答案均由程序校验）</p>

<div class="mask" id="cloudMask">
  <div class="sheet">
    <div class="sheethead"><h3>跨设备同步</h3><span class="close" id="cloudClose">关闭</span></div>
    <div id="cloudBody" style="padding:4px 2px 12px"></div>
    <div class="sheetbar">
      <button class="btn main" id="cloudLogin">使用 WorkBuddy 登录</button>
      <button class="btn" id="cloudSyncNow" style="display:none">立即同步</button>
      <button class="btn" id="cloudLogout" style="display:none">退出登录</button>
    </div>
  </div>
</div>

<!-- 云 SDK 内联注入：国内访问 cdn.jsdelivr.net 会失败，不能外链 -->
<script>__CLOUD_SDK__</script>
<script>
const QUIZ = __QUIZ__;
const VOCAB = __VOCAB__;
const KNOW = __KNOW__;
const MATH = __MATH__;
const YANYU = __YANYU__;
const CLOUD = __CLOUD__;
const PAPERS = QUIZ.papers;

const APIQ = 'http://127.0.0.1:8760/api/progress';
const APIV = 'http://127.0.0.1:8760/api/vocab';
const APIK = 'http://127.0.0.1:8760/api/know';
const APIM = 'http://127.0.0.1:8760/api/math';
const APIY = 'http://127.0.0.1:8760/api/yanyu';
const AKEY = 'gdquiz2-answers', FKEY = 'gdquiz2-favs', UKEY = 'gdquiz2-updated';
const VFKEY = 'gdvocab-favs', VUKEY = 'gdvocab-updated';
const KFKEY = 'gdknow-favs', KUKEY = 'gdknow-updated';
const MSKEY = 'gdmath-stat', MFKEY = 'gdmath-favs', MUKEY = 'gdmath-updated', MLKEY = 'gdmath-last';
const YSKEY = 'gdyan-stat', YFKEY = 'gdyan-favs', YUKEY = 'gdyan-updated', YLKEY = 'gdyan-last';
const $ = s => document.querySelector(s);

/* ================= 状态 ================= */
let answers = {}, favs = {};
try { answers = JSON.parse(localStorage.getItem(AKEY) || '{}'); } catch(e){ answers = {}; }
try { favs = JSON.parse(localStorage.getItem(FKEY) || '{}'); } catch(e){ favs = {}; }
let qAt = Number(localStorage.getItem(UKEY) || 0) || 0;

let vfavs = {};
try { vfavs = JSON.parse(localStorage.getItem(VFKEY) || '{}'); } catch(e){ vfavs = {}; }
let vAt = Number(localStorage.getItem(VUKEY) || 0) || 0;

let kfavs = {};
try { kfavs = JSON.parse(localStorage.getItem(KFKEY) || '{}'); } catch(e){ kfavs = {}; }
let kAt = Number(localStorage.getItem(KUKEY) || 0) || 0;

let mstat = {};
try { mstat = JSON.parse(localStorage.getItem(MSKEY) || '{}'); } catch(e){ mstat = {}; }
let mfavs = {};
try { mfavs = JSON.parse(localStorage.getItem(MFKEY) || '{}'); } catch(e){ mfavs = {}; }
let mAt = Number(localStorage.getItem(MUKEY) || 0) || 0;
let mLast = null;
try { mLast = JSON.parse(localStorage.getItem(MLKEY) || 'null'); } catch(e){ mLast = null; }

let ystat = {};
try { ystat = JSON.parse(localStorage.getItem(YSKEY) || '{}'); } catch(e){ ystat = {}; }
let yfavs = {};
try { yfavs = JSON.parse(localStorage.getItem(YFKEY) || '{}'); } catch(e){ yfavs = {}; }
let yAt = Number(localStorage.getItem(YUKEY) || 0) || 0;
let yLast = null;
try { yLast = JSON.parse(localStorage.getItem(YLKEY) || 'null'); } catch(e){ yLast = null; }

// 迁移旧单期页（gdquiz-<id> / gdquiz-<id>-fav）
(function(){
  try{
    const ks = [];
    for(let i=0;i<localStorage.length;i++) ks.push(localStorage.key(i));
    ks.forEach(k => {
      if(!k.startsWith('gdquiz-')) return;
      const body = k.slice(7);
      let o = {};
      try { o = JSON.parse(localStorage.getItem(k) || '{}'); } catch(e){ return; }
      if(body.endsWith('-fav')){
        const p = body.slice(0,-4);
        if(!PAPERS.some(x => x.id === p)) return;
        Object.keys(o).forEach(n => { if(o[n]) favs[p + ':' + n] = 1; });
      } else {
        if(!PAPERS.some(x => x.id === body)) return;
        Object.keys(o).forEach(n => { if(o[n]) answers[body + ':' + n] = o[n]; });
      }
    });
  }catch(e){}
})();

/* ================= 同步 ================= */
const IS_LOCAL = (location.hostname === '127.0.0.1' || location.hostname === 'localhost');
// 云端登录的 callback_url 有域名白名单（github.io 会被中继挡成 400），
// 所以只有主站能登录；GitHub Pages 那份只当随手可开的镜像。
const SYNC_HOST = 'wbapp-cmvrw789ihbe3hosa43jcr.app.workbuddy.host';
const PRIMARY_URL = 'https://wbapp-cmvrw789ihbe3hosa43jcr.app.workbuddy.host/?sharecode=XD7NFFZQ3Y';
const CAN_SYNC = (location.hostname === SYNC_HOST);
const sync = { q:'idle', v:'idle', k:'idle', m:'idle', y:'idle' };
const syncMsg = { q:'', v:'', k:'', m:'', y:'' };
function setSync(){
  const el = $('#sync');
  const all = [sync.q, sync.v, sync.k, sync.m, sync.y];
  const isLocalOnly = (all.every(x => x === 'local')) && cloudState.mode !== 'cloud';
  const bad = all.some(x => x === 'off');
  const okAll = all.every(x => x === 'ok');
  el.className = 'sync ' + (bad ? 'off' : (okAll ? 'ok' : ''));
  if(isLocalOnly){
    el.textContent = '本机保存';
    el.title = '进度存在这台设备的浏览器里，还没同步到云端。点右边「登录同步」可跨设备。';
    return;
  }
  el.textContent = bad ? '未连服务器 · 点击重试'
                : (okAll ? '已同步 ' + new Date().toLocaleTimeString('zh-CN',{hour12:false}) : '连接中…');
  el.title = bad
    ? ('连不上 http://127.0.0.1:8760 ｜ ' + (syncMsg.q || syncMsg.v || syncMsg.k || syncMsg.m || '') +
       '\n进度仍存在本机浏览器，刷题不受影响。双击「启动服务器.vbs」或点这里重试。')
    : '进度与收藏同步到本机 127.0.0.1:8760';
}
$('#sync').onclick = () => {
  sync.q = sync.v = sync.k = sync.m = 'idle';
  syncMsg.q = syncMsg.v = syncMsg.k = syncMsg.m = '';
  setSync();
  pullAll();
};

let seq = 0;
function getJSON(url){
  const ctl = new AbortController();
  const t = setTimeout(() => { try{ ctl.abort(); }catch(e){} }, 7000);
  return fetch(url, {cache:'no-store', signal: ctl.signal})
    .then(r => r.json())
    .finally(() => clearTimeout(t));
}

function post(url, body, which){
  if(!IS_LOCAL){ sync[which] = 'local'; setSync(); return Promise.resolve({ ok:false, local:true }); }
  return getJSON2(url, body)
    .then(res => { sync[which] = 'ok'; setSync(); return res; })
    .catch(e => { sync[which] = 'off'; syncMsg[which] = 'POST 失败：' + (e && e.name || 'x'); setSync(); throw 0; });
}
function getJSON2(url, body){
  const ctl = new AbortController();
  const t = setTimeout(() => { try{ ctl.abort(); }catch(e){} }, 7000);
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body), signal: ctl.signal})
    .then(r => r.json())
    .finally(() => clearTimeout(t));
}

function saveQuiz(){
  qAt = Date.now();
  try { localStorage.setItem(AKEY, JSON.stringify(answers)); localStorage.setItem(FKEY, JSON.stringify(favs)); localStorage.setItem(UKEY, String(qAt)); } catch(e){}
  post(APIQ, {answers, favs, updatedAt: qAt}, 'q').catch(() => {});
  cloudTouch();
}
function saveVocab(){
  vAt = Date.now();
  try { localStorage.setItem(VFKEY, JSON.stringify(vfavs)); localStorage.setItem(VUKEY, String(vAt)); } catch(e){}
  post(APIV, {answers:{}, favs: vfavs, updatedAt: vAt}, 'v').catch(() => {});
  cloudTouch();
}
function saveKnow(){
  kAt = Date.now();
  try { localStorage.setItem(KFKEY, JSON.stringify(kfavs)); localStorage.setItem(KUKEY, String(kAt)); } catch(e){}
  post(APIK, {answers:{}, favs: kfavs, updatedAt: kAt}, 'k').catch(() => {});
  cloudTouch();
}
function saveMath(){
  mAt = Date.now();
  try {
    localStorage.setItem(MSKEY, JSON.stringify(mstat));
    localStorage.setItem(MFKEY, JSON.stringify(mfavs));
    localStorage.setItem(MUKEY, String(mAt));
  } catch(e){}
  post(APIM, {answers: mstat, favs: mfavs, updatedAt: mAt}, 'm').catch(() => {});
  cloudTouch();
}
function saveYan(){
  yAt = Date.now();
  try {
    localStorage.setItem(YSKEY, JSON.stringify(ystat));
    localStorage.setItem(YFKEY, JSON.stringify(yfavs));
    localStorage.setItem(YUKEY, String(yAt));
  } catch(e){}
  post(APIY, {answers: ystat, favs: yfavs, updatedAt: yAt}, 'y').catch(() => {});
  cloudTouch();
}

function pullAll(){
  if(!IS_LOCAL){
    sync.q = sync.v = sync.k = sync.m = sync.y = 'local';
    setSync();
    renderHome();
    return;
  }
  setSync();
  getJSON(APIQ + '?t=' + Date.now()).then(s => {
    sync.q = 'ok';
    const at = Number(s.updatedAt || 0) || 0;
    if(at > qAt + 500){
      answers = s.answers || {}; favs = s.favs || {}; qAt = at;
      try { localStorage.setItem(AKEY, JSON.stringify(answers)); localStorage.setItem(FKEY, JSON.stringify(favs)); localStorage.setItem(UKEY, String(qAt)); } catch(e){}
      if(state.view === 'quiz'){ buildQuizList(); renderQuiz(); buildTabs(); }
    } else if(qAt > at && (Object.keys(answers).length || Object.keys(favs).length)){
      saveQuiz();
    }
    setSync(); renderHome();
  }).catch(e => { sync.q = 'off'; syncMsg.q = 'GET progress 失败：' + (e && e.name || 'x'); setSync(); });

  getJSON(APIV + '?t=' + Date.now()).then(s => {
    sync.v = 'ok';
    const at = Number(s.updatedAt || 0) || 0;
    if(at > vAt + 500){
      vfavs = s.favs || {}; vAt = at;
      try { localStorage.setItem(VFKEY, JSON.stringify(vfavs)); localStorage.setItem(VUKEY, String(vAt)); } catch(e){}
      if(state.view === 'vocab'){ buildVocabChips(); buildVocabList(); renderVocab(); }
    } else if(vAt > at && Object.keys(vfavs).length){
      saveVocab();
    }
    setSync(); renderHome();
  }).catch(e => { sync.v = 'off'; syncMsg.v = 'GET vocab 失败：' + (e && e.name || 'x'); setSync(); });

  getJSON(APIK + '?t=' + Date.now()).then(s => {
    sync.k = 'ok';
    const at = Number(s.updatedAt || 0) || 0;
    if(at > kAt + 500){
      kfavs = s.favs || {}; kAt = at;
      try { localStorage.setItem(KFKEY, JSON.stringify(kfavs)); localStorage.setItem(KUKEY, String(kAt)); } catch(e){}
      if(state.view === 'know'){ buildKnowChips(); buildKnowList(); renderKnow(); }
    } else if(kAt > at && Object.keys(kfavs).length){
      saveKnow();
    }
    setSync(); renderHome();
  }).catch(e => { sync.k = 'off'; syncMsg.k = 'GET know 失败：' + (e && e.name || 'x'); setSync(); });

  getJSON(APIM + '?t=' + Date.now()).then(s => {
    sync.m = 'ok';
    const at = Number(s.updatedAt || 0) || 0;
    if(at > mAt + 500){
      mstat = s.answers || {}; mfavs = s.favs || {}; mAt = at;
      try {
        localStorage.setItem(MSKEY, JSON.stringify(mstat));
        localStorage.setItem(MFKEY, JSON.stringify(mfavs));
        localStorage.setItem(MUKEY, String(mAt));
      } catch(e){}
      if(state.view === 'math') renderMathHome();
    } else if(mAt > at && (Object.keys(mstat).length || Object.keys(mfavs).length)){
      saveMath();
    }
    setSync(); renderHome();
  }).catch(e => { sync.m = 'off'; syncMsg.m = 'GET math 失败：' + (e && e.name || 'x'); setSync(); });

  getJSON(APIY + '?t=' + Date.now()).then(s => {
    sync.y = 'ok';
    const at = Number(s.updatedAt || 0) || 0;
    if(at > yAt + 500){
      ystat = s.answers || {}; yfavs = s.favs || {}; yAt = at;
      try {
        localStorage.setItem(YSKEY, JSON.stringify(ystat));
        localStorage.setItem(YFKEY, JSON.stringify(yfavs));
        localStorage.setItem(YUKEY, String(yAt));
      } catch(e){}
      if(state.view === 'yanyu') renderYanHome();
    } else if(yAt > at && (Object.keys(ystat).length || Object.keys(yfavs).length)){
      saveYan();
    }
    setSync(); renderHome();
  }).catch(e => { sync.y = 'off'; syncMsg.y = 'GET yanyu 失败：' + (e && e.name || 'x'); setSync(); });
}
/* ================= 路由 ================= */
const state = { view:'home', pid:'', filter:'all', pos:0, list:[],
                vmode:'card', vfilter:'all', vkw:'', vpos:0, vlist:[], vopen:false,
                kmode:'card', kfilter:'all', kkw:'', kpos:0, klist:[], khide:false };

const VIEWS = ['home','quiz','vocab','know','math','yanyu'];
const VIEWNAME = {home:'总览', quiz:'每日刷题', vocab:'成语速记', know:'知识点速记', math:'数量关系', yanyu:'言语理解'};

function go(view){
  state.view = view;
  VIEWS.forEach(v => { $('#v-' + v).style.display = (v === view ? '' : 'none'); });
  document.querySelectorAll('#nav button').forEach(b => b.classList.toggle('on', b.dataset.go === view));
  $('#sub').textContent = VIEWNAME[view];
  if(location.hash !== '#' + view) history.replaceState(null, '', '#' + view);
  window.scrollTo({top:0});
  if(view === 'home') renderHome();
  if(view === 'quiz'){ buildDates(); buildTabs(); renderQuiz(); }
  if(view === 'vocab'){ buildVocabChips(); buildVocabList(); renderVocab(); }
  if(view === 'know'){ buildKnowChips(); buildKnowList(); renderKnow(); }
  if(view === 'math'){ renderMathHome(); renderMathView(); }
  if(view === 'yanyu'){ renderYanHome(); renderYanView(); }
}

document.querySelectorAll('[data-go]').forEach(b => { b.onclick = () => go(b.dataset.go); });
window.addEventListener('hashchange', () => {
  const v = location.hash.replace('#','');
  if(VIEWS.includes(v) && v !== state.view) go(v);
});

/* ================= 刷题 ================= */
const qkey = q => q.pid + ':' + q.n;
const curPaper = () => PAPERS.find(p => p.id === state.pid) || PAPERS[PAPERS.length - 1];
state.pid = PAPERS.length ? PAPERS[PAPERS.length - 1].id : '';

function buildQuizList(){
  const p = curPaper();
  if(!p){ state.list = []; return; }
  let qs = p.questions;
  if(state.filter === 'fav'){
    const out = [];
    PAPERS.forEach(pp => pp.questions.forEach(q => {
      if(favs[pp.id + ':' + q.n]) out.push(Object.assign({}, q, {pid:pp.id, issue:pp.issue, date:pp.date}));
    }));
    state.list = out;
    return;
  }
  if(state.filter !== 'all') qs = qs.filter(q => q.sec === state.filter);
  state.list = qs.map(q => Object.assign({}, q, {pid:p.id, issue:p.issue, date:p.date}));
}

function buildDates(){
  const box = $('#dates');
  box.innerHTML = '';
  PAPERS.forEach(p => {
    const b = document.createElement('button');
    b.className = 'date' + (p.id === state.pid ? ' on' : '');
    b.innerHTML = '<b>' + p.date.slice(5) + '</b><small>' + p.issue + '</small>';
    b.onclick = () => { state.pid = p.id; state.filter = 'all'; state.pos = 0; buildDates(); buildTabs(); buildQuizList(); renderQuiz(); };
    box.appendChild(b);
  });
}

function buildTabs(){
  const box = $('#tabs');
  box.innerHTML = '';
  const p = curPaper();
  const mk = (label, val, on) => {
    const b = document.createElement('button');
    b.className = 'tab' + (on ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { state.filter = val; state.pos = 0; buildQuizList(); renderQuiz(); buildTabs(); };
    box.appendChild(b);
  };
  mk('全部 ' + (p ? p.questions.length : 0), 'all', state.filter === 'all');
  mk('★ 收藏 ' + Object.keys(favs).length, 'fav', state.filter === 'fav');
  if(p) p.sections.forEach(sec => mk(sec.short, sec.name, state.filter === sec.name));
}

function renderQuiz(){
  const q = state.list[state.pos];
  if(!q){
    $('#qno').textContent = '—'; $('#qsec').textContent = '暂无题目'; $('#qfrom').style.display = 'none';
    $('#qtext').textContent = state.filter === 'fav'
      ? '还没有收藏的题目。点题目右上角的 ☆ 可以收藏，这里的收藏会跨期汇总。'
      : '这里还没有题目。';
    $('#opts').innerHTML = ''; $('#exp').classList.remove('show'); $('#star').style.visibility = 'hidden';
    $('#pos').textContent = ''; $('#prev').disabled = true; $('#next').disabled = true;
    return;
  }
  $('#star').style.visibility = 'visible';
  const on = !!favs[qkey(q)];
  $('#star').textContent = on ? '★' : '☆';
  $('#star').classList.toggle('on', on);
  $('#star').onclick = () => {
    if(favs[qkey(q)]) delete favs[qkey(q)]; else favs[qkey(q)] = 1;
    saveQuiz();
    if(state.filter === 'fav'){ buildQuizList(); if(state.pos > state.list.length - 1) state.pos = Math.max(0, state.list.length - 1); }
    renderQuiz(); buildTabs(); renderHome();
  };

  $('#qno').textContent = '第 ' + q.n + ' 题';
  $('#qsec').textContent = q.sec;
  const fr = $('#qfrom');
  if(q.pid !== state.pid){ fr.style.display = ''; fr.textContent = '第 ' + q.issue + ' 期 · ' + q.date.slice(5); }
  else fr.style.display = 'none';
  $('#qtext').textContent = q.q;

  const sel = answers[qkey(q)];
  const box = $('#opts');
  box.innerHTML = '';
  ['A','B','C','D'].forEach((k, i) => {
    const b = document.createElement('button');
    b.className = 'opt';
    b.innerHTML = '<span class="k">' + k + '</span><span class="t"></span>';
    b.querySelector('.t').textContent = q.opts[i] || '';
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
  } else exp.classList.remove('show');

  $('#pos').textContent = (state.pos + 1) + ' / ' + state.list.length;
  $('#prev').disabled = state.pos === 0;
  $('#next').disabled = state.pos === state.list.length - 1;
  $('#sheetBtn').textContent = '答题卡 ' + state.list.length;
}

function choose(k){
  const q = state.list[state.pos];
  if(!q || answers[qkey(q)]) return;
  answers[qkey(q)] = k;
  saveQuiz();
  renderQuiz(); renderHome();
}

function goQ(step){
  if(!state.list.length) return;
  const n = state.pos + step;
  if(n < 0 || n >= state.list.length) return;
  state.pos = n; renderQuiz();
}

$('#prev').onclick = () => goQ(-1);
$('#next').onclick = () => goQ(1);

function buildGrid(){
  const g = $('#grid');
  g.innerHTML = '';
  const cur = state.list[state.pos] ? qkey(state.list[state.pos]) : '';
  $('#sheetTitle').textContent = state.filter === 'fav' ? '答题卡 · 全部收藏' : '答题卡 · 第 ' + curPaper().issue + ' 期';
  state.list.forEach(q => {
    const c = document.createElement('div');
    c.className = 'cell';
    c.textContent = q.n;
    const a = answers[qkey(q)];
    if(a) c.classList.add(a === q.ans ? 'ok' : 'bad');
    if(favs[qkey(q)]) c.classList.add('fav');
    if(qkey(q) === cur) c.classList.add('cur');
    c.onclick = () => { state.pos = state.list.findIndex(x => qkey(x) === qkey(q)); renderQuiz(); closeSheet(); };
    g.appendChild(c);
  });
}
function openSheet(){ $('#mask').classList.add('show'); document.body.style.overflow = 'hidden'; buildGrid(); }
function closeSheet(){ $('#mask').classList.remove('show'); document.body.style.overflow = ''; }
$('#sheetBtn').onclick = openSheet;
$('#closeSheet').onclick = closeSheet;
$('#closeTop').onclick = closeSheet;
$('#mask').onclick = e => { if(e.target === $('#mask')) closeSheet(); };

$('#jumpWrong').onclick = () => {
  const after = state.list.findIndex((q, i) => i > state.pos && answers[qkey(q)] && answers[qkey(q)] !== q.ans);
  if(after >= 0){ state.pos = after; renderQuiz(); closeSheet(); return; }
  const any = state.list.findIndex(q => answers[qkey(q)] && answers[qkey(q)] !== q.ans);
  if(any >= 0){ state.pos = any; renderQuiz(); closeSheet(); }
  else alert('当前范围内没有错题。');
};

$('#resetAll').onclick = () => {
  const label = state.filter === 'fav' ? '收藏夹' : ('第 ' + curPaper().issue + ' 期');
  if(confirm('清空' + label + '的答题记录？（收藏不受影响）')){
    state.list.forEach(q => { delete answers[qkey(q)]; });
    saveQuiz(); state.pos = 0; renderQuiz(); renderHome();
  }
};

$('#expBtn').onclick = () => {
  const pad = n => String(n).padStart(2,'0');
  const d = new Date();
  const data = { app:'gdquiz', v:5, exportedAt:d.toISOString(), answers, favs, vfavs, kfavs, mstat, mfavs, ystat, yfavs };
  const blob = new Blob([JSON.stringify(data, null, 1)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '省考平台_记录_' + d.getFullYear() + pad(d.getMonth()+1) + pad(d.getDate()) + '.json';
  document.body.appendChild(a); a.click(); a.remove();
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
      if(!o || typeof o !== 'object') throw 0;
      let na = 0, nf = 0, nv = 0, nk = 0;
      Object.keys(o.answers || {}).forEach(k => { if(!answers[k] && o.answers[k]){ answers[k] = o.answers[k]; na++; } });
      Object.keys(o.favs || {}).forEach(k => { if(!favs[k] && o.favs[k]){ favs[k] = 1; nf++; } });
      Object.keys(o.vfavs || {}).forEach(k => { if(!vfavs[k] && o.vfavs[k]){ vfavs[k] = 1; nv++; } });
      Object.keys(o.kfavs || {}).forEach(k => { if(!kfavs[k] && o.kfavs[k]){ kfavs[k] = 1; nk++; } });
      Object.keys(o.mfavs || {}).forEach(k => { if(!mfavs[k] && o.mfavs[k]){ mfavs[k] = 1; nk++; } });
      Object.keys(o.mstat || {}).forEach(k => { if(!mstat[k] && o.mstat[k]){ mstat[k] = o.mstat[k]; nk++; } });
      Object.keys(o.yfavs || {}).forEach(k => { if(!yfavs[k] && o.yfavs[k]){ yfavs[k] = 1; nk++; } });
      Object.keys(o.ystat || {}).forEach(k => { if(!ystat[k] && o.ystat[k]){ ystat[k] = o.ystat[k]; nk++; } });
      saveQuiz(); saveVocab(); saveKnow(); saveMath(); saveYan(); closeSheet();
      buildQuizList(); renderQuiz(); buildTabs();
      buildVocabChips(); buildVocabList(); renderVocab();
      buildKnowChips(); buildKnowList(); renderKnow();
      renderMathHome(); renderYanHome(); renderHome();
      alert('已恢复：作答 ' + na + ' 题、题目收藏 ' + nf + ' 条、成语收藏 ' + nv + ' 条、知识点/数量关系/言语理解收藏与记录 ' + nk + ' 条。');
    }catch(err){ alert('这个文件读不出来，请选择本平台导出的 json。'); }
    e.target.value = '';
  };
  rd.readAsText(f);
};

/* ================= 成语 ================= */
function buildVocabList(){
  state.vlist = VOCAB.filter(it => {
    if(state.vfilter === 'fav' && !vfavs[it.w]) return false;
    if(state.vfilter === 'len4' && it.w.length !== 4) return false;
    if(state.vfilter === 'len2' && it.w.length !== 2) return false;
    if(state.vfilter === 'other' && (it.w.length === 4 || it.w.length === 2)) return false;
    if(state.vkw){
      const k = state.vkw;
      if(!(it.w.includes(k) || it.d.toLowerCase().includes(k.toLowerCase()))) return false;
    }
    return true;
  });
  if(state.vpos > state.vlist.length - 1) state.vpos = 0;
}

function buildVocabChips(){
  const box = $('#vchips');
  box.innerHTML = '';
  [['all','全部 ' + VOCAB.length], ['fav','★ 收藏 ' + Object.keys(vfavs).length],
   ['len4','四字成语'], ['len2','两字词'], ['other','其他']].forEach(([c,label]) => {
    const b = document.createElement('button');
    b.className = 'chip' + (state.vfilter === c ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { state.vfilter = c; state.vpos = 0; buildVocabChips(); buildVocabList(); renderVocab(); };
    box.appendChild(b);
  });
}

function renderVocab(){
  if(state.vmode === 'card'){ $('#vCardView').style.display = ''; $('#vListView').style.display = 'none'; renderVocabCard(); }
  else { $('#vCardView').style.display = 'none'; $('#vListView').style.display = ''; renderVocabList(); }
}

function renderVocabCard(){
  const it = state.vlist[state.vpos];
  const card = $('#vcard');
  if(!it){
    $('#vword').textContent = '—'; $('#vdef').textContent = ''; $('#vtags').innerHTML = '';
    $('#vpos').textContent = '没有符合条件的成语'; $('#vstar').style.visibility = 'hidden';
    card.classList.remove('open'); return;
  }
  $('#vstar').style.visibility = 'visible';
  const on = !!vfavs[it.w];
  $('#vstar').textContent = on ? '★' : '☆';
  $('#vstar').classList.toggle('on', on);
  $('#vword').textContent = it.w;
  $('#vdef').textContent = it.d;
  $('#vtags').innerHTML = '<span></span>';
  $('#vtags span').textContent = it.w.length === 4 ? '四字成语' : (it.w.length === 2 ? '两字词' : it.w.length + ' 字');
  card.classList.toggle('open', state.vopen);
  $('#vpos').textContent = (state.vpos + 1) + ' / ' + state.vlist.length;
}

function renderVocabList(){
  const g = $('#vgrid');
  g.innerHTML = '';
  $('#vempty').style.display = state.vlist.length ? 'none' : '';
  const frag = document.createDocumentFragment();
  state.vlist.forEach(it => {
    const d = document.createElement('div');
    d.className = 'vitem clip';
    const on = !!vfavs[it.w];
    d.innerHTML = '<div class="w"></div><div class="d"></div><span class="k' + (on ? ' on' : '') + '">' + (on ? '★' : '☆') + '</span>';
    d.querySelector('.w').textContent = it.w;
    d.querySelector('.d').textContent = it.d;
    d.onclick = e => {
      if(e.target.classList.contains('k')){ toggleVFav(it.w); return; }
      d.classList.toggle('clip');
    };
    frag.appendChild(d);
  });
  g.appendChild(frag);
}

function toggleVFav(w){
  if(vfavs[w]) delete vfavs[w]; else vfavs[w] = 1;
  saveVocab();
  buildVocabChips();
  if(state.vfilter === 'fav'){ buildVocabList(); if(state.vpos > state.vlist.length - 1) state.vpos = Math.max(0, state.vlist.length - 1); }
  renderVocab(); renderHome();
}

function goV(step){
  if(!state.vlist.length) return;
  state.vpos = (state.vpos + step + state.vlist.length) % state.vlist.length;
  state.vopen = false; renderVocabCard();
}
$('#vprev').onclick = () => goV(-1);
$('#vnext').onclick = () => goV(1);
$('#vshuffle').onclick = () => {
  if(!state.vlist.length) return;
  state.vpos = Math.floor(Math.random() * state.vlist.length);
  state.vopen = false; renderVocabCard();
};
$('#vreveal').onclick = () => { state.vopen = !state.vopen; $('#vcard').classList.toggle('open', state.vopen); };
$('#vcard').onclick = e => {
  if(e.target.id === 'vstar') return;
  state.vopen = !state.vopen;
  $('#vcard').classList.toggle('open', state.vopen);
};
$('#vstar').onclick = e => { e.stopPropagation(); if(state.vlist[state.vpos]) toggleVFav(state.vlist[state.vpos].w); };
$('#vmCard').onclick = () => { state.vmode = 'card'; $('#vmCard').classList.add('on'); $('#vmList').classList.remove('on'); renderVocab(); };
$('#vmList').onclick = () => { state.vmode = 'list'; $('#vmList').classList.add('on'); $('#vmCard').classList.remove('on'); renderVocab(); };
$('#vq').oninput = e => { state.vkw = e.target.value.trim(); state.vpos = 0; buildVocabList(); renderVocab(); };

/* ================= 知识点 ================= */
const KCAT = [];
KNOW.forEach(k => { if(!KCAT.some(c => c.id === k.cat)) KCAT.push({id:k.cat, name:k.cname}); });

function buildKnowList(){
  const kw = state.kkw.toLowerCase();
  state.klist = KNOW.filter(it => {
    if(state.kfilter === 'fav' && !kfavs[it.id]) return false;
    if(state.kfilter !== 'all' && state.kfilter !== 'fav' && it.cat !== state.kfilter) return false;
    if(kw){
      const hay = (it.t + ' ' + it.items.join(' ') + ' ' + (it.note || '') + ' ' + it.cname).toLowerCase();
      if(!hay.includes(kw)) return false;
    }
    return true;
  });
  if(state.kpos > state.klist.length - 1) state.kpos = 0;
}

function buildKnowChips(){
  const box = $('#kchips');
  box.innerHTML = '';
  const rows = [['all','全部 ' + KNOW.length], ['fav','★ 收藏 ' + Object.keys(kfavs).length]]
    .concat(KCAT.map(c => [c.id, c.name + ' ' + KNOW.filter(k => k.cat === c.id).length]));
  rows.forEach(([c,label]) => {
    const b = document.createElement('button');
    b.className = 'chip' + (state.kfilter === c ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { state.kfilter = c; state.kpos = 0; buildKnowChips(); buildKnowList(); renderKnow(); };
    box.appendChild(b);
  });
}

function renderKnow(){
  if(state.kmode === 'card'){
    $('#kCardView').style.display = ''; $('#kListView').style.display = 'none';
    renderKnowCard();
  } else {
    $('#kCardView').style.display = 'none'; $('#kListView').style.display = '';
    renderKnowList();
  }
}

function renderKnowCard(){
  const it = state.klist[state.kpos];
  const card = $('#kcard');
  if(!it){
    $('#kt').textContent = '—'; $('#kitems').innerHTML = '';
    $('#knote').style.display = 'none'; $('#ksrc').textContent = '';
    $('#kpos').textContent = '没有符合条件的知识点';
    $('#kstar').style.visibility = 'hidden';
    card.classList.remove('hide');
    return;
  }
  $('#kstar').style.visibility = 'visible';
  const on = !!kfavs[it.id];
  $('#kstar').textContent = on ? '★' : '☆';
  $('#kstar').classList.toggle('on', on);

  $('#kt').innerHTML = '';
  const t = document.createElement('div');
  t.textContent = it.t;
  t.style.cssText = 'display:inline';
  $('#kt').appendChild(t);
  const c = document.createElement('span');
  c.className = 'kc'; c.textContent = it.cname; c.style.marginLeft = '8px';
  $('#kt').appendChild(c);
  if(it.tag){
    const g = document.createElement('span');
    g.className = 'ktag'; g.textContent = it.tag;
    $('#kt').appendChild(g);
  }

  const ol = $('#kitems');
  ol.innerHTML = '';
  it.items.forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    ol.appendChild(li);
  });

  const nt = $('#knote');
  if(it.note){ nt.style.display = ''; nt.textContent = '易错／记法：' + it.note; }
  else { nt.style.display = 'none'; nt.textContent = ''; }
  $('#ksrc').textContent = it.src ? '出处：' + it.src : '';
  card.classList.toggle('hide', !!state.khide);
  $('#kpos').textContent = (state.kpos + 1) + ' / ' + state.klist.length;
}

function renderKnowList(){
  const g = $('#kgrid');
  g.innerHTML = '';
  $('#kempty').style.display = state.klist.length ? 'none' : '';
  const frag = document.createDocumentFragment();
  state.klist.forEach(it => {
    const d = document.createElement('div');
    d.className = 'kitem';
    const on = !!kfavs[it.id];
    d.innerHTML = '<div class="kt2"></div><div class="kc2"></div><div class="kb"></div>' +
                  '<span class="k' + (on ? ' on' : '') + '">' + (on ? '★' : '☆') + '</span>';
    d.querySelector('.kt2').textContent = it.t;
    d.querySelector('.kc2').textContent = it.cname + (it.tag ? '　·　' + it.tag : '');
    const kb = d.querySelector('.kb');
    it.items.forEach(s => {
      const sp = document.createElement('span');
      sp.textContent = s;
      kb.appendChild(sp);
    });
    d.onclick = e => {
      if(e.target.classList.contains('k')){ toggleKFav(it.id); return; }
      state.kpos = Math.max(0, state.klist.findIndex(x => x.id === it.id));
      state.kmode = 'card';
      $('#kmCard').classList.add('on'); $('#kmList').classList.remove('on');
      renderKnow();
      window.scrollTo({top:0});
    };
    frag.appendChild(d);
  });
  g.appendChild(frag);
}

function toggleKFav(id){
  if(kfavs[id]) delete kfavs[id]; else kfavs[id] = 1;
  saveKnow();
  buildKnowChips();
  if(state.kfilter === 'fav'){ buildKnowList(); if(state.kpos > state.klist.length - 1) state.kpos = Math.max(0, state.klist.length - 1); }
  renderKnow(); renderHome();
}

function goK(step){
  if(!state.klist.length) return;
  state.kpos = (state.kpos + step + state.klist.length) % state.klist.length;
  renderKnowCard();
}
$('#kprev').onclick = () => goK(-1);
$('#knext').onclick = () => goK(1);
$('#kshuffle').onclick = () => {
  if(!state.klist.length) return;
  state.kpos = Math.floor(Math.random() * state.klist.length);
  renderKnowCard();
};
$('#kreveal').onclick = () => { state.khide = !state.khide; $('#kcard').classList.toggle('hide', state.khide); };
$('#khide').onclick = () => {
  state.khide = !state.khide;
  $('#khide').classList.toggle('on', state.khide);
  $('#kcard').classList.toggle('hide', state.khide);
};
$('#kcard').onclick = e => {
  if(e.target.id === 'kstar') return;
  state.khide = !state.khide;
  $('#kcard').classList.toggle('hide', state.khide);
};
$('#kstar').onclick = e => { e.stopPropagation(); if(state.klist[state.kpos]) toggleKFav(state.klist[state.kpos].id); };
$('#kmCard').onclick = () => { state.kmode = 'card'; $('#kmCard').classList.add('on'); $('#kmList').classList.remove('on'); renderKnow(); };
$('#kmList').onclick = () => { state.kmode = 'list'; $('#kmList').classList.add('on'); $('#kmCard').classList.remove('on'); renderKnow(); };
$('#kq').oninput = e => { state.kkw = e.target.value.trim(); state.kpos = 0; buildKnowList(); renderKnow(); };

/* ================= 数量关系 ================= */
const MSET_N = 10;
let mset = null;              // {ids, pos, pick, t0, mode}
let mView = 'start';          // start | run | done
let mTimerId = 0;
let mCat = 'all';             // 题型筛选：all / 工程问题 / 集合容斥

const MCATS = Array.from(new Set(MATH.map(x => x.cat || '工程问题')));
const mBase = () => (mCat === 'all' ? MATH : MATH.filter(x => (x.cat || '工程问题') === mCat));

const mById = id => MATH.find(x => x.id === id);

function shuffle(a){
  const b = a.slice();
  for(let i = b.length - 1; i > 0; i--){
    const j = Math.floor(Math.random() * (i + 1));
    const t = b[i]; b[i] = b[j]; b[j] = t;
  }
  return b;
}

function pickIds(mode){
  const base = mBase();
  if(mode === 'fav'){
    return shuffle(base.filter(x => mfavs[x.id]).map(x => x.id)).slice(0, MSET_N);
  }
  const fresh = base.filter(x => !mstat[x.id]).map(x => x.id);
  const done = base.filter(x => mstat[x.id]).map(x => x.id);
  let out = shuffle(fresh);
  if(out.length < MSET_N) out = out.concat(shuffle(done));
  return out.slice(0, MSET_N);
}

function buildMathChips(){
  const box = $('#mchips');
  if(!box) return;
  box.innerHTML = '';
  const rows = [['all', '全部 ' + MATH.length]]
    .concat(MCATS.map(c => [c, c + ' ' + MATH.filter(x => (x.cat || '工程问题') === c).length]));
  rows.forEach(([c, label]) => {
    const b = document.createElement('button');
    b.className = 'chip' + (mCat === c ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { mCat = c; renderMathHome(); };
    box.appendChild(b);
  });
}

function startSet(mode){
  const ids = pickIds(mode);
  if(!ids.length){
    const scope = mCat === 'all' ? '' : '「' + mCat + '」里';
    alert(mode === 'fav' ? scope + '还没有收藏的题。先做一组，点题目右上角的 ☆ 收藏几道。' : '题库是空的。');
    return;
  }
  mset = { ids, pos: 0, pick: {}, t0: Date.now(), mode };
  mView = 'run';
  startTimer();
  renderMathView();
  renderM();
  window.scrollTo({top:0});
}

function startTimer(){
  clearInterval(mTimerId);
  const tick = () => {
    const s = Math.floor((Date.now() - (mset ? mset.t0 : Date.now())) / 1000);
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    $('#mTimer').textContent = mm + ':' + ss;
  };
  tick();
  mTimerId = setInterval(tick, 1000);
}
function stopTimer(){ clearInterval(mTimerId); mTimerId = 0; }

function renderMathView(){
  $('#mStart').style.display = mView === 'start' ? '' : 'none';
  $('#mRun').style.display = mView === 'run' ? '' : 'none';
  $('#mDone').style.display = mView === 'done' ? '' : 'none';
}

function buildMDots(){
  const box = $('#mdots');
  box.innerHTML = '';
  if(!mset) return;
  mset.ids.forEach((id, i) => {
    const el = document.createElement('i');
    el.textContent = i + 1;
    const pick = mset.pick[id];
    if(pick){ el.classList.add(pick === ['A','B','C','D'][mById(id).ans] ? 'r' : 'w'); }
    if(i === mset.pos) el.classList.add('cur');
    el.onclick = () => { mset.pos = i; renderM(); };
    box.appendChild(el);
  });
}

function renderM(){
  if(!mset) return;
  const id = mset.ids[mset.pos];
  const q = mById(id);
  $('#mTot').textContent = mset.ids.length;
  $('#mIdx').textContent = mset.pos + 1;
  $('#mno').textContent = '第 ' + (mset.pos + 1) + ' 题';
  $('#mtag').textContent = q.tag + '　·　' + (q.lv === 1 ? '基础' : (q.lv === 2 ? '进阶' : '拔高'));
  $('#mqtext').textContent = q.t;

  const on = !!mfavs[id];
  $('#mstar').textContent = on ? '★' : '☆';
  $('#mstar').classList.toggle('on', on);
  $('#mstar').onclick = () => {
    if(mfavs[id]) delete mfavs[id]; else mfavs[id] = 1;
    saveMath(); renderM(); renderMathHome(); renderHome();
  };

  const sel = mset.pick[id];
  const box = $('#mopts');
  box.innerHTML = '';
  ['A','B','C','D'].forEach((k, i) => {
    const b = document.createElement('button');
    b.className = 'opt';
    b.innerHTML = '<span class="k">' + k + '</span><span class="t"></span>';
    b.querySelector('.t').textContent = q.opts[i] || '';
    if(sel){
      b.classList.add('done');
      if(i === q.ans) b.classList.add('correct');
      else if(k === sel) b.classList.add('wrong');
      else b.classList.add('dim');
    } else {
      b.onclick = () => chooseM(k);
    }
    box.appendChild(b);
  });

  const exp = $('#mexp');
  if(sel){
    exp.classList.add('show');
    const ok = ['A','B','C','D'][q.ans] === sel;
    const v = $('#mverdict');
    v.className = 'verdict ' + (ok ? 'ok' : 'bad');
    v.innerHTML = (ok ? '✓ 回答正确' : '✗ 回答错误') + '<span class="badge">正确答案 ' + ['A','B','C','D'][q.ans] + '</span>';
    $('#mexpl').textContent = q.exp || '';
  } else {
    exp.classList.remove('show');
  }
  buildMDots();
}

function chooseM(k){
  if(!mset) return;
  const id = mset.ids[mset.pos];
  if(mset.pick[id]) return;
  const q = mById(id);
  mset.pick[id] = k;
  mstat[id] = (k === ['A','B','C','D'][q.ans]) ? 'r' : 'w';
  saveMath();
  renderM();
  renderMathHome();
  renderHome();
}

function goM(step){
  if(!mset) return;
  mset.pos = (mset.pos + step + mset.ids.length) % mset.ids.length;
  renderM();
}

function finishM(){
  if(!mset) return;
  stopTimer();
  const total = mset.ids.length;
  let right = 0;
  const wrongIds = [];
  mset.ids.forEach(id => {
    const pick = mset.pick[id];
    const q = mById(id);
    if(pick && pick === ['A','B','C','D'][q.ans]) right++;
    else if(pick) wrongIds.push(id);
  });
  const used = Math.round((Date.now() - mset.t0) / 1000);
  mLast = { at: Date.now(), total, right, used, wrongIds, answered: Object.keys(mset.pick).length };
  try { localStorage.setItem(MLKEY, JSON.stringify(mLast)); } catch(e){}
  mView = 'done';

  $('#mScoreT').textContent = '本组 ' + right + ' / ' + total;
  const rate = Math.round(right / total * 100);
  $('#mScoreS').textContent = rate >= 80 ? '稳了，这个正确率考场够用。'
    : rate >= 60 ? '基本盘在，错的那几道记一下是哪一步算错的。'
    : '工程题先别求快，把「设总量＝最小公倍数」这一步固化下来。';
  $('#mRight').textContent = right;
  $('#mWrong').textContent = total - right;
  $('#mUsed').textContent = Math.floor(used / 60) + '分' + (used % 60) + '秒';

  const box = $('#mWrongList');
  box.innerHTML = '';
  if(!wrongIds.length){
    box.innerHTML = '<div class="prow" style="cursor:default"><div class="i">这一组没有错题。</div></div>';
  } else {
    wrongIds.forEach(id => {
      const q = mById(id);
      const row = document.createElement('div');
      row.className = 'prow';
      row.innerHTML = '<div><div class="d" style="font-size:13.5px;line-height:1.7"></div>' +
                      '<div class="i">你的答案 ' + mset.pick[id] + '　正确答案 ' + ['A','B','C','D'][q.ans] + '　·　' + q.tag + '</div></div>' +
                      '<div class="meta">重看 →</div>';
      row.querySelector('.d').textContent = q.t.length > 46 ? q.t.slice(0, 46) + '…' : q.t;
      row.onclick = () => { mset.pos = mset.ids.indexOf(id); mView = 'run'; renderMathView(); renderM(); window.scrollTo({top:0}); };
      box.appendChild(row);
    });
  }
  renderMathView();
  renderMathHome();
  renderHome();
  window.scrollTo({top:0});
}

function renderMathHome(){
  buildMathChips();
  const base = mBase();
  const pool = base.length;
  const done = base.filter(x => mstat[x.id]).length;
  let r = 0;
  base.forEach(x => { if(mstat[x.id] === 'r') r++; });
  if($('#mPool')) $('#mPool').textContent = pool;
  $('#mDoneN').textContent = done;
  $('#mFavN').textContent = base.filter(x => mfavs[x.id]).length;
  $('#mRate').textContent = done ? Math.round(r / done * 100) + '%' : '—';

  const box = $('#mLast');
  if(!mLast){
    box.innerHTML = '<div class="prow" style="cursor:default"><div class="i">还没做过。点上面的按钮随机来一组 10 道。</div></div>';
  } else {
    const d = new Date(mLast.at);
    box.innerHTML = '<div class="prow" style="cursor:default"><div><div class="d">' + mLast.right + ' / ' + mLast.total +
      '　正确率 ' + Math.round(mLast.right / mLast.total * 100) + '%</div>' +
      '<div class="i">' + (d.getMonth() + 1) + '月' + d.getDate() + '日 ' +
      String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') +
      '　用时 ' + Math.floor(mLast.used / 60) + '分' + (mLast.used % 60) + '秒' +
      (mLast.wrongIds && mLast.wrongIds.length ? '　错 ' + mLast.wrongIds.length + ' 道' : '') + '</div></div>' +
      '<div class="meta">' + (mLast.wrongIds && mLast.wrongIds.length ? '回看 →' : '') + '</div></div>';
    if(mLast.wrongIds && mLast.wrongIds.length){
      box.querySelector('.prow').onclick = () => {
        mset = { ids: mLast.wrongIds.slice(), pos: 0, pick: {}, t0: Date.now(), mode: 'review' };
        mView = 'run'; startTimer(); renderMathView(); renderM();
      };
    }
  }
}

$('#mStartBtn').onclick = () => startSet('random');
$('#mFavBtn').onclick = () => startSet('fav');
$('#mAgain').onclick = () => startSet('random');
$('#mBack').onclick = () => { mView = 'start'; mset = null; renderMathView(); renderMathHome(); };
$('#mprev').onclick = () => goM(-1);
$('#mnext').onclick = () => goM(1);
$('#mfinish').onclick = () => finishM();
$('#mquit').onclick = () => {
  if(Object.keys(mset.pick).length && !confirm('本组还没交卷，退出后这一组的作答不记录成绩（已作答的题仍算做过）。确定退出？')) return;
  stopTimer(); mset = null; mView = 'start'; renderMathView(); renderMathHome(); renderHome();
};
$('#mResetBtn').onclick = () => {
  if(!confirm('清空数量关系的做题记录与收藏？（其他模块不受影响）')) return;
  mstat = {}; mfavs = {}; mLast = null;
  try { localStorage.removeItem(MLKEY); } catch(e){}
  saveMath(); renderMathHome(); renderHome();
};


/* ================= 言语理解 ================= */
const YSET_N = 10;
let yset = null;
let yView = 'start';
let yTimerId = 0;
let yCat = 'all';

const YCATS = Array.from(new Set(YANYU.map(x => x.cat)));
const yBase = () => (yCat === 'all' ? YANYU : YANYU.filter(x => x.cat === yCat));
const yById = id => YANYU.find(x => x.id === id);
const YLET = ['A','B','C','D'];

function pickYIds(mode){
  const base = yBase();
  if(mode === 'fav'){
    return shuffle(base.filter(x => yfavs[x.id]).map(x => x.id)).slice(0, YSET_N);
  }
  const fresh = base.filter(x => !ystat[x.id]).map(x => x.id);
  const done = base.filter(x => ystat[x.id]).map(x => x.id);
  let out = shuffle(fresh);
  if(out.length < YSET_N) out = out.concat(shuffle(done));
  return out.slice(0, YSET_N);
}

function buildYanChips(){
  const box = $('#ychips');
  if(!box) return;
  box.innerHTML = '';
  const rows = [['all', '全部 ' + YANYU.length]]
    .concat(YCATS.map(c => [c, c + ' ' + YANYU.filter(x => x.cat === c).length]));
  rows.forEach(([c, label]) => {
    const b = document.createElement('button');
    b.className = 'chip' + (yCat === c ? ' on' : '');
    b.textContent = label;
    b.onclick = () => { yCat = c; renderYanHome(); };
    box.appendChild(b);
  });
}

function startYanSet(mode){
  const ids = pickYIds(mode);
  if(!ids.length){
    const scope = yCat === 'all' ? '' : '「' + yCat + '」里';
    alert(mode === 'fav' ? scope + '还没有收藏的题。先做一组，点题目右上角的 ☆ 收藏几道。' : '题库是空的。');
    return;
  }
  yset = { ids, pos: 0, pick: {}, t0: Date.now(), mode };
  yView = 'run';
  startYTimer();
  renderYanView();
  renderY();
  window.scrollTo({top:0});
}

function startYTimer(){
  clearInterval(yTimerId);
  const tick = () => {
    const s = Math.floor((Date.now() - (yset ? yset.t0 : Date.now())) / 1000);
    $('#yTimer').textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
  };
  tick();
  yTimerId = setInterval(tick, 1000);
}
function stopYTimer(){ clearInterval(yTimerId); yTimerId = 0; }

function renderYanView(){
  $('#yStart').style.display = yView === 'start' ? '' : 'none';
  $('#yRun').style.display = yView === 'run' ? '' : 'none';
  $('#yDone').style.display = yView === 'done' ? '' : 'none';
}

function buildYDots(){
  const box = $('#ydots');
  box.innerHTML = '';
  if(!yset) return;
  yset.ids.forEach((id, i) => {
    const el = document.createElement('i');
    el.textContent = i + 1;
    const pick = yset.pick[id];
    if(pick) el.classList.add(pick === YLET[yById(id).ans] ? 'r' : 'w');
    if(i === yset.pos) el.classList.add('cur');
    el.onclick = () => { yset.pos = i; renderY(); };
    box.appendChild(el);
  });
}

function renderY(){
  if(!yset) return;
  const id = yset.ids[yset.pos];
  const q = yById(id);
  $('#yTot').textContent = yset.ids.length;
  $('#yIdx').textContent = yset.pos + 1;
  $('#yno').textContent = '第 ' + (yset.pos + 1) + ' 题';
  $('#ytag').textContent = q.cat + '　·　' + q.tag;
  $('#yqtext').textContent = q.t;

  const on = !!yfavs[id];
  $('#ystar').textContent = on ? '★' : '☆';
  $('#ystar').classList.toggle('on', on);
  $('#ystar').onclick = () => {
    if(yfavs[id]) delete yfavs[id]; else yfavs[id] = 1;
    saveYan(); renderY(); renderYanHome(); renderHome();
  };

  const sel = yset.pick[id];
  const box = $('#yopts');
  box.innerHTML = '';
  YLET.forEach((k, i) => {
    const b = document.createElement('button');
    b.className = 'opt';
    b.innerHTML = '<span class="k"></span><span class="t"></span>';
    b.querySelector('.k').textContent = k;
    b.querySelector('.t').textContent = q.opts[i] || '';
    if(sel){
      b.classList.add('done');
      if(i === q.ans) b.classList.add('correct');
      else if(k === sel) b.classList.add('wrong');
      else b.classList.add('dim');
    } else {
      b.onclick = () => chooseY(k);
    }
    box.appendChild(b);
  });

  const exp = $('#yexp');
  if(sel){
    exp.classList.add('show');
    const ok = YLET[q.ans] === sel;
    const v = $('#yverdict');
    v.className = 'verdict ' + (ok ? 'ok' : 'bad');
    v.innerHTML = (ok ? '✓ 回答正确' : '✗ 回答错误') + '<span class="badge">正确答案 ' + YLET[q.ans] + '</span>';
    $('#yexpl').textContent = q.exp || '';
  } else {
    exp.classList.remove('show');
  }
  buildYDots();
}

function chooseY(k){
  if(!yset) return;
  const id = yset.ids[yset.pos];
  if(yset.pick[id]) return;
  const q = yById(id);
  yset.pick[id] = k;
  ystat[id] = (k === YLET[q.ans]) ? 'r' : 'w';
  saveYan();
  renderY();
  renderYanHome();
  renderHome();
}

function goY(step){
  if(!yset) return;
  yset.pos = (yset.pos + step + yset.ids.length) % yset.ids.length;
  renderY();
}

function finishY(){
  if(!yset) return;
  stopYTimer();
  const total = yset.ids.length;
  let right = 0;
  const wrongIds = [];
  yset.ids.forEach(id => {
    const pick = yset.pick[id];
    const q = yById(id);
    if(pick && pick === YLET[q.ans]) right++;
    else if(pick) wrongIds.push(id);
  });
  const used = Math.round((Date.now() - yset.t0) / 1000);
  yLast = { at: Date.now(), total, right, used, wrongIds, answered: Object.keys(yset.pick).length };
  try { localStorage.setItem(YLKEY, JSON.stringify(yLast)); } catch(e){}
  yView = 'done';

  $('#yScoreT').textContent = '本组 ' + right + ' / ' + total;
  const rate = Math.round(right / total * 100);
  $('#yScoreS').textContent = rate >= 80 ? '稳了，这个正确率考场够用。'
    : rate >= 60 ? '基本盘在，错的题回去看解析里「为什么排除」那一句。'
    : '言语理解靠的是题干对应，先把每个错误选项的排除理由读一遍。';
  $('#yRight').textContent = right;
  $('#yWrong').textContent = total - right;
  $('#yUsed').textContent = Math.floor(used / 60) + '分' + (used % 60) + '秒';

  const box = $('#yWrongList');
  box.innerHTML = '';
  if(!wrongIds.length){
    box.innerHTML = '<div class="prow" style="cursor:default"><div class="i">这一组没有错题。</div></div>';
  } else {
    wrongIds.forEach(id => {
      const q = yById(id);
      const row = document.createElement('div');
      row.className = 'prow';
      row.innerHTML = '<div><div class="d" style="font-size:13.5px;line-height:1.7"></div>' +
                      '<div class="i"></div></div><div class="meta">重看 →</div>';
      const d = q.t.replace(/\n/g, ' ');
      row.querySelector('.d').textContent = d.length > 46 ? d.slice(0, 46) + '…' : d;
      row.querySelector('.i').textContent = '你的答案 ' + yset.pick[id] + '　正确答案 ' + YLET[q.ans] + '　·　' + q.cat + '／' + q.tag;
      row.onclick = () => { yset.pos = yset.ids.indexOf(id); yView = 'run'; renderYanView(); renderY(); window.scrollTo({top:0}); };
      box.appendChild(row);
    });
  }
  renderYanView();
  renderYanHome();
  renderHome();
  window.scrollTo({top:0});
}

function renderYanHome(){
  buildYanChips();
  const base = yBase();
  const done = base.filter(x => ystat[x.id]).length;
  let r = 0;
  base.forEach(x => { if(ystat[x.id] === 'r') r++; });
  if($('#yPool')) $('#yPool').textContent = base.length;
  if($('#yDoneN')) $('#yDoneN').textContent = done;
  if($('#yFavN')) $('#yFavN').textContent = base.filter(x => yfavs[x.id]).length;
  if($('#yRate')) $('#yRate').textContent = done ? Math.round(r / done * 100) + '%' : '—';

  const box = $('#yLast');
  if(!box) return;
  if(!yLast){
    box.innerHTML = '<div class="prow" style="cursor:default"><div class="i">还没做过。点上面的按钮随机来一组 10 道。</div></div>';
  } else {
    const d = new Date(yLast.at);
    box.innerHTML = '<div class="prow" style="cursor:default"><div><div class="d">' + yLast.right + ' / ' + yLast.total +
      '　正确率 ' + Math.round(yLast.right / yLast.total * 100) + '%</div>' +
      '<div class="i">' + (d.getMonth() + 1) + '月' + d.getDate() + '日 ' +
      String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') +
      '　用时 ' + Math.floor(yLast.used / 60) + '分' + (yLast.used % 60) + '秒' +
      (yLast.wrongIds && yLast.wrongIds.length ? '　错 ' + yLast.wrongIds.length + ' 道' : '') + '</div></div>' +
      '<div class="meta">' + (yLast.wrongIds && yLast.wrongIds.length ? '回看 →' : '') + '</div></div>';
    if(yLast.wrongIds && yLast.wrongIds.length){
      box.querySelector('.prow').onclick = () => {
        yset = { ids: yLast.wrongIds.slice(), pos: 0, pick: {}, t0: Date.now(), mode: 'review' };
        yView = 'run'; startYTimer(); renderYanView(); renderY();
      };
    }
  }
}

$('#yStartBtn').onclick = () => startYanSet('random');
$('#yFavBtn').onclick = () => startYanSet('fav');
$('#yAgain').onclick = () => startYanSet('random');
$('#yBack').onclick = () => { yView = 'start'; yset = null; renderYanView(); renderYanHome(); };
$('#yprev').onclick = () => goY(-1);
$('#ynext').onclick = () => goY(1);
$('#yfinish').onclick = () => finishY();
$('#yquit').onclick = () => {
  if(yset && Object.keys(yset.pick).length && !confirm('本组还没交卷，退出后这一组的作答不记录成绩（已作答的题仍算做过）。确定退出？')) return;
  stopYTimer(); yset = null; yView = 'start'; renderYanView(); renderYanHome(); renderHome();
};
$('#yResetBtn').onclick = () => {
  if(!confirm('清空言语理解的做题记录与收藏？（其他模块不受影响）')) return;
  ystat = {}; yfavs = {}; yLast = null;
  try { localStorage.removeItem(YLKEY); } catch(e){}
  saveYan(); renderYanHome(); renderHome();
};


/* ================= 云端同步（仅线上） ================= */
const cloudState = { mode:'local', ready:false, session:null, err:'', busy:false, remoteFilled:false };
let cloud = null;
let pushTimer = 0;

const localMaxAt = () => Math.max(qAt || 0, vAt || 0, kAt || 0, mAt || 0, yAt || 0);

// 空态判断：换设备登录时最怕拿一张空表把云端冲掉，所以空的一律不算"更新"
const isBlank = o => !o || Object.keys(o).length === 0;
const localEmpty = () => isBlank(answers) && isBlank(favs) && isBlank(vfavs)
  && isBlank(kfavs) && isBlank(mstat) && isBlank(mfavs)
  && isBlank(ystat) && isBlank(yfavs);
const payloadEmpty = p => !p || (isBlank(p.answers) && isBlank(p.favs) && isBlank(p.vfavs)
  && isBlank(p.kfavs) && isBlank(p.mstat) && isBlank(p.mfavs)
  && isBlank(p.ystat) && isBlank(p.yfavs));

function cloudInit(){
  if(!CLOUD || IS_LOCAL || !window.WorkBuddyCloud){
    cloudState.err = IS_LOCAL ? '本地调试不连云端' : '云 SDK 未加载';
    return false;
  }
  if(!CAN_SYNC){
    cloudState.err = '这个地址是镜像页，登录同步只支持主站';
    return false;
  }
  cloud = WorkBuddyCloud.createWorkBuddyCloud({
    endpoint: CLOUD.endpoint,
    oauthRelayBaseUrl: CLOUD.oauthRelayBaseUrl,
    publishableKey: CLOUD.publishableKey
  });
  cloudState.ready = true;
  return true;
}

function setMode(mode){
  cloudState.mode = mode;
  const v = mode === 'cloud' ? 'ok' : 'local';
  sync.q = sync.v = sync.k = sync.m = v;
  setSync();
}

async function restoreAuth(){
  const url = new URL(location.href);
  const hasCb = url.searchParams.has('code') || url.searchParams.has('error');
  if(!hasCb){
    try{
      const { data } = await cloud.auth.getSession();
      cloudState.session = data || null;
    }catch(e){ cloudState.err = '读取登录状态失败'; }
    return;
  }
  // 中继回跳时不一定带 provider，只有 code 就默认按 WorkBuddy 处理
  const provider = (url.searchParams.get('provider') || 'workbuddy').toLowerCase();
  if(provider !== 'workbuddy' && provider !== 'wechat'){
    cloudState.err = '授权回调缺少有效的登录方式，请重新登录。';
    return;
  }
  const fn = provider === 'workbuddy' ? cloud.auth.handleWorkBuddyCallback : cloud.auth.handleWechatWebCallback;
  if(typeof fn !== 'function'){
    cloudState.err = '当前版本暂不支持该登录方式。';
    return;
  }
  try{
    const { data: session, error } = await fn.call(cloud.auth);
    if(error){ cloudState.err = error.message || '登录失败'; return; }
    cloudState.session = session || null;
  }catch(e){ cloudState.err = '登录回调处理失败'; return; }
  finally{
    // 无论成功失败都清掉一次性参数，否则刷新页面会反复用同一个 code
    ['code','state','provider'].forEach(k => url.searchParams.delete(k));
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }
}

function applyPayload(p){
  if(!p || typeof p !== 'object') return;
  answers = p.answers || {}; favs = p.favs || {};
  vfavs = p.vfavs || {}; kfavs = p.kfavs || {};
  mstat = p.mstat || {}; mfavs = p.mfavs || {};
  ystat = p.ystat || {}; yfavs = p.yfavs || {};
  const at = Number(p.updatedAt || 0) || Date.now();
  qAt = vAt = kAt = mAt = yAt = at;
  try{
    localStorage.setItem(AKEY, JSON.stringify(answers));
    localStorage.setItem(FKEY, JSON.stringify(favs));
    localStorage.setItem(UKEY, String(qAt));
    localStorage.setItem(VFKEY, JSON.stringify(vfavs));
    localStorage.setItem(VUKEY, String(vAt));
    localStorage.setItem(KFKEY, JSON.stringify(kfavs));
    localStorage.setItem(KUKEY, String(kAt));
    localStorage.setItem(MSKEY, JSON.stringify(mstat));
    localStorage.setItem(MFKEY, JSON.stringify(mfavs));
    localStorage.setItem(MUKEY, String(mAt));
    localStorage.setItem(YSKEY, JSON.stringify(ystat));
    localStorage.setItem(YFKEY, JSON.stringify(yfavs));
    localStorage.setItem(YUKEY, String(yAt));
  }catch(e){}
  buildQuizList(); buildTabs && buildTabs(); renderQuiz && renderQuiz();
  buildVocabChips(); buildVocabList(); renderVocab();
  buildKnowChips(); buildKnowList(); renderKnow();
  renderMathHome(); renderYanHome && renderYanHome(); renderHome();
}

async function cloudPull(){
  if(!cloud || !cloudState.session) return;
  cloudState.busy = true;
  try{
    const { data, error } = await cloud.database
      .from('study_state').select('payload').maybeSingle();
    if(error){ cloudState.err = error.message; setMode('local'); return; }
    const p = data && data.payload;
    cloudState.remoteFilled = !!p && !payloadEmpty(p);
    if(!p){
      await cloudPush();                      // 首次登录：把本机记录推上去
    } else if(localEmpty() && cloudState.remoteFilled){
      applyPayload(p);                        // 新设备什么都没做：先认云端的，别拿空表覆盖
      cloudState.err = '';
      setMode('cloud');
    } else if((Number(p.updatedAt || 0) || 0) > localMaxAt()){
      applyPayload(p);                        // 云端更新：覆盖本机
      cloudState.err = '';
      setMode('cloud');
    } else {
      await cloudPush();                      // 本机更新：推到云端
    }
    cloudState.err = '';
    setMode('cloud');
  }catch(e){
    cloudState.err = '拉取云端记录失败';
    setMode('local');
  }finally{
    cloudState.busy = false;
    updateAcct();
  }
}

async function cloudPush(){
  if(!cloud || !cloudState.session) return;
  // 本机一片空白而云端有货：多半是新设备刚登录，别把云端冲掉
  if(localEmpty() && cloudState.remoteFilled) return;
  const payload = { answers, favs, vfavs, kfavs, mstat, mfavs, ystat, yfavs, updatedAt: Date.now() };
  const name = (cloudState.session.user && cloudState.session.user.name) || null;
  try{
    const { error } = await cloud.database.from('study_state').upsert(
      { payload, owner_name: name, updated_at: new Date().toISOString() },
      { onConflict: 'owner_id' }
    );
    if(error){ cloudState.err = error.message; setMode('local'); return; }
    cloudState.err = '';
    setMode('cloud');
  }catch(e){
    cloudState.err = '上传失败，进度仍保存在本机';
    setMode('local');
  }
  updateAcct();
}

function cloudTouch(){
  if(!cloud || !cloudState.session) return;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(cloudPush, 1500);
}

function updateAcct(){
  const b = $('#acctBtn');
  if(!b) return;
  if(!CLOUD || IS_LOCAL){ b.style.display = 'none'; return; }
  b.style.display = '';
  b.textContent = !CAN_SYNC ? '去主站同步' : (cloudState.session ? '已登录' : '登录同步');
  b.title = !CAN_SYNC
    ? '这个地址是镜像页，云端同步要去主站'
    : (cloudState.session ? '已连接云端，进度会自动同步到其他设备' : '登录后，手机和电脑共用一份进度');
  const body = $('#cloudBody');
  if(!CAN_SYNC){
    body.innerHTML = '<p style="font-size:14px;line-height:1.9;color:#374151;margin:0 0 10px">' +
      '这里是 GitHub 上的镜像页，只用来随手打开刷题，不连云端——登录回跳只认主站域名。</p>' +
      '<p style="font-size:13px;line-height:1.9;color:#374151;margin:0">' +
      '要跨设备同步，去主站登录：<br><a href="' + PRIMARY_URL + '" style="color:#b45309;word-break:break-all">' + PRIMARY_URL + '</a></p>';
    $('#cloudLogin').textContent = '打开主站';
    $('#cloudLogin').style.display = '';
    $('#cloudSyncNow').style.display = 'none';
    $('#cloudLogout').style.display = 'none';
    return;
  }
  $('#cloudLogin').textContent = '使用 WorkBuddy 登录';
  if(!cloudState.session){
    body.innerHTML = '<p style="font-size:14px;line-height:1.9;color:#374151;margin:0 0 10px">' +
      '现在进度只存在这台设备的浏览器里。登录后会上传一份到云端，其它设备登录同一个账号就能接着做。</p>' +
      '<p style="font-size:12.5px;line-height:1.8;color:#6b7280;margin:0">' +
      '首次登录时，本机已有的记录会作为初始数据上传；之后按时间取较新的一份，不会互相覆盖成空。</p>' +
      (cloudState.err
        ? '<p style="font-size:12.5px;line-height:1.8;color:#b91c1c;margin:10px 0 0">⚠ ' + cloudState.err + '</p>'
        : '');
    $('#cloudLogin').style.display = '';
    $('#cloudSyncNow').style.display = 'none';
    $('#cloudLogout').style.display = 'none';
  }else{
    const u = cloudState.session.user || {};
    body.innerHTML = '<p style="font-size:14px;line-height:1.9;color:#374151;margin:0 0 6px">' +
      '已登录：<b>' + (u.name || u.email || u.phone || '当前账号') + '</b></p>' +
      '<p style="font-size:12.5px;line-height:1.8;color:#6b7280;margin:0">' +
      (cloudState.err ? '⚠ ' + cloudState.err : '进度已与云端同步，做一题会自动保存。') + '</p>';
    $('#cloudLogin').style.display = 'none';
    $('#cloudSyncNow').style.display = '';
    $('#cloudLogout').style.display = '';
    $('#cloudLogout').textContent = '退出登录';
  }
}

$('#acctBtn').onclick = () => { updateAcct(); $('#cloudMask').classList.add('show'); };
$('#cloudClose').onclick = () => $('#cloudMask').classList.remove('show');
$('#cloudMask').onclick = e => { if(e.target.id === 'cloudMask') $('#cloudMask').classList.remove('show'); };
$('#cloudLogin').onclick = async () => {
  if(!CAN_SYNC){ location.href = PRIMARY_URL; return; }
  if(!cloud){ alert('云服务还没就绪，刷新页面再试。'); return; }
  const back = new URL(location.href);
  back.pathname = '/';
  ['code','state','provider'].forEach(k => back.searchParams.delete(k));
  try{
    const { data, error } = await cloud.auth.signInWithOAuth({ provider:'workbuddy', redirectTo: back.toString() });
    if(error){ alert('登录发起失败：' + (error.message || '')); return; }
    location.assign(data.url);
  }catch(e){ alert('登录发起失败，请稍后重试。'); }
};
$('#cloudSyncNow').onclick = async () => {
  const b = $('#cloudSyncNow');
  b.textContent = '同步中…'; b.disabled = true;
  await cloudPull();
  b.textContent = '立即同步'; b.disabled = false;
  updateAcct();
};
$('#cloudLogout').onclick = async () => {
  try{ await cloud.auth.signOut(); }catch(e){}
  cloudState.session = null;
  cloudState.err = '';
  setMode('local');
  updateAcct();
  renderHome();
};

async function cloudBoot(){
  // 探针：无头验证时读 <html data-cloud> 判断 SDK 是否真的加载了
  document.documentElement.dataset.cloud = window.WorkBuddyCloud ? 'sdk-ok' : 'sdk-missing';
  if(!CAN_SYNC && !IS_LOCAL){
    // 镜像页（GitHub Pages）：不连云端，只提示去主站
    document.documentElement.dataset.cloud = 'mirror';
    setMode('local'); updateAcct(); return;
  }
  if(!cloudInit()) { setMode('local'); document.documentElement.dataset.cloud = cloudState.err; return; }
  await restoreAuth();
  if(cloudState.session){
    await cloudPull();
  } else {
    setMode('local');
  }
  updateAcct();
  document.documentElement.dataset.cloud = cloudState.session ? 'signed-in' : 'signed-out';
  // 切回标签页时拉一次：手机做完几题，电脑这边切回来就能看到
  document.addEventListener('visibilitychange', () => {
    if(document.visibilityState === 'visible' && cloudState.session && !cloudState.busy){
      cloudPull().then(updateAcct);
    }
  });
}

/* ================= 首页 ================= */
function quizStats(){
  let total = 0, done = 0, right = 0;
  PAPERS.forEach(p => p.questions.forEach(q => {
    total++;
    const a = answers[p.id + ':' + q.n];
    if(a){ done++; if(a === q.ans) right++; }
  }));
  return {total, done, right, rate: done ? Math.round(right / done * 100) : null};
}

function renderHome(){
  const s = quizStats();
  const vf = Object.keys(vfavs).length;
  $('#doneN').textContent = s.done;
  $('#totalN').textContent = s.total;
  $('#rate').textContent = s.rate === null ? '—' : s.rate + '%';
  $('#rate').style.color = s.rate === null ? '#9ca3af' : (s.rate >= 80 ? '#15803d' : (s.rate >= 60 ? '#b45309' : '#b91c1c'));
  $('#favN').textContent = Object.keys(favs).length;
  $('#vfavN').textContent = vf;
  const kf = Object.keys(kfavs).length;
  $('#kfavN').textContent = kf;
  const mf = Object.keys(mfavs).length;
  const mDone = MATH.filter(x => mstat[x.id]).length;
  $('#mfavN').textContent = mf;
  const yf = Object.keys(yfavs).length;
  const yDone = YANYU.filter(x => ystat[x.id]).length;
  if($('#yfavN')) $('#yfavN').textContent = yf;

  $('#hDone').innerHTML = s.done + '<small> / ' + s.total + '</small>';
  $('#hRate').textContent = s.rate === null ? '—' : s.rate + '%';
  $('#hFav').innerHTML = Object.keys(favs).length + '<small> 题</small>';
  $('#hVocab').innerHTML = vf + '<small> / ' + VOCAB.length + '</small>';
  $('#hKnow').innerHTML = kf + '<small> / ' + KNOW.length + '</small>';
  const pct = s.done / (s.total || 1) * 100;
  $('#tQuizDone').innerHTML = s.done + '<small> 题已答</small>';
  $('#tQuizBar').style.width = pct.toFixed(1) + '%';
  $('#tVocabFav').innerHTML = vf + '<small> 条已收藏</small>';
  $('#tVocabBar').style.width = (vf / (VOCAB.length || 1) * 100).toFixed(1) + '%';
  $('#tKnowFav').innerHTML = kf + '<small> 条已收藏</small>';
  $('#tKnowBar').style.width = (kf / (KNOW.length || 1) * 100).toFixed(1) + '%';
  $('#tMathDone').innerHTML = mDone + '<small> 道已做</small>';
  $('#tMathBar').style.width = (mDone / (MATH.length || 1) * 100).toFixed(1) + '%';
  if($('#hYan')) $('#hYan').innerHTML = yf + '<small> 道</small>';
  if($('#tYanDone')) $('#tYanDone').innerHTML = yDone + '<small> 道已做</small>';
  if($('#tYanBar')) $('#tYanBar').style.width = (yDone / (YANYU.length || 1) * 100).toFixed(1) + '%';

  const box = $('#paperList');
  box.innerHTML = '';
  PAPERS.slice().reverse().forEach(p => {
    let d = 0, r = 0;
    p.questions.forEach(q => { const a = answers[p.id + ':' + q.n]; if(a){ d++; if(a === q.ans) r++; } });
    const row = document.createElement('div');
    row.className = 'prow';
    const dotCls = d === 0 ? '' : (d === p.questions.length ? 'done' : 'part');
    row.innerHTML = '<span class="dot ' + dotCls + '"></span><div><div class="d">' + p.date + '　第 ' + p.issue + ' 期</div>' +
                    '<div class="i">' + p.questions.length + ' 题　' + p.sections.length + ' 个小节</div></div>' +
                    '<div class="meta">' + d + ' / ' + p.questions.length + (d ? '<br>' + Math.round(r / d * 100) + '%' : '') + '</div>';
    row.onclick = () => { state.pid = p.id; state.filter = 'all'; state.pos = 0; go('quiz'); };
    box.appendChild(row);
  });

  const favList = $('#favPreview');
  const picks = VOCAB.filter(it => vfavs[it.w]).slice(0, 4);
  if(!picks.length){
    favList.innerHTML = '<div class="prow" style="cursor:default"><div class="i">还没有收藏的成语，去「成语速记」点 ☆ 收藏几条，考前只看这些。</div></div>';
  } else {
    favList.innerHTML = '';
    picks.forEach(it => {
      const row = document.createElement('div');
      row.className = 'prow';
      row.innerHTML = '<div><div class="d">' + it.w + '</div><div class="i" style="max-width:520px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + it.d.slice(0, 40) + '</div></div>' +
                      '<div class="meta">查看 →</div>';
      row.onclick = () => { state.vfilter = 'fav'; state.vpos = Math.max(0, state.vlist.findIndex(x => x.w === it.w)); go('vocab'); };
      favList.appendChild(row);
    });
  }

  const kBox = $('#kfavPreview');
  const kPicks = KNOW.filter(it => kfavs[it.id]).slice(0, 4);
  if(!kPicks.length){
    kBox.innerHTML = '<div class="prow" style="cursor:default"><div class="i">还没有收藏的知识点。去「知识点」翻几张卡，点 ☆ 收下背不下来的那几条。</div></div>';
  } else {
    kBox.innerHTML = '';
    kPicks.forEach(it => {
      const row = document.createElement('div');
      row.className = 'prow';
      row.innerHTML = '<div><div class="d">' + it.t + '</div><div class="i" style="max-width:520px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + it.items.join('　') + '</div></div>' +
                      '<div class="meta">查看 →</div>';
      row.onclick = () => { state.kfilter = 'fav'; buildKnowList(); state.kpos = Math.max(0, state.klist.findIndex(x => x.id === it.id)); go('know'); };
      kBox.appendChild(row);
    });
  }
}

/* ================= 键盘 ================= */
document.addEventListener('keydown', e => {
  if(e.target.tagName === 'INPUT') return;
  if(e.key === 'Escape'){ closeSheet(); return; }
  if(state.view === 'quiz'){
    const k = e.key.toUpperCase();
    if(['1','2','3','4'].includes(k)) choose(['A','B','C','D'][+k - 1]);
    else if(['A','B','C','D'].includes(k)) choose(k);
    else if(k === 'F'){ const b = $('#star'); if(b && b.style.visibility !== 'hidden') b.click(); }
    else if(e.key === 'ArrowLeft') goQ(-1);
    else if(e.key === 'ArrowRight') goQ(1);
  } else if(state.view === 'vocab'){
    if(e.key === 'ArrowLeft') goV(-1);
    else if(e.key === 'ArrowRight') goV(1);
    else if(e.key === ' '){ e.preventDefault(); state.vopen = !state.vopen; $('#vcard').classList.toggle('open', state.vopen); }
    else if(e.key === 'F' || e.key === 'f'){ if(state.vlist[state.vpos]) toggleVFav(state.vlist[state.vpos].w); }
  } else if(state.view === 'know'){
    if(e.key === 'ArrowLeft') goK(-1);
    else if(e.key === 'ArrowRight') goK(1);
    else if(e.key === ' '){ e.preventDefault(); state.khide = !state.khide; $('#kcard').classList.toggle('hide', state.khide); }
    else if(e.key === 'F' || e.key === 'f'){ if(state.klist[state.kpos]) toggleKFav(state.klist[state.kpos].id); }
  } else if(state.view === 'math' && mView === 'run' && mset){
    const k = e.key.toUpperCase();
    if(['1','2','3','4'].includes(k)) chooseM(['A','B','C','D'][+k - 1]);
    else if(['A','B','C','D'].includes(k)) chooseM(k);
    else if(e.key === 'ArrowLeft') goM(-1);
    else if(e.key === 'ArrowRight') goM(1);
    else if(k === 'F'){ const id = mset.ids[mset.pos]; if(mfavs[id]) delete mfavs[id]; else mfavs[id] = 1; saveMath(); renderM(); renderHome(); }
  } else if(state.view === 'yanyu' && yView === 'run' && yset){
    const k = e.key.toUpperCase();
    if(['1','2','3','4'].includes(k)) chooseY(['A','B','C','D'][+k - 1]);
    else if(['A','B','C','D'].includes(k)) chooseY(k);
    else if(e.key === 'ArrowLeft') goY(-1);
    else if(e.key === 'ArrowRight') goY(1);
    else if(k === 'F'){ const id = yset.ids[yset.pos]; if(yfavs[id]) delete yfavs[id]; else yfavs[id] = 1; saveYan(); renderY(); renderHome(); }
  }
});

/* ================= 启动 ================= */
const startView = VIEWS.includes(location.hash.replace('#','')) ? location.hash.replace('#','') : 'home';
buildQuizList();
renderHome();
go(startView);
pullAll();
cloudBoot();
setInterval(pullAll, 60000);
document.addEventListener('visibilitychange', () => { if(!document.hidden) pullAll(); });
</script>
</body>
</html>
"""


def load_cloud() -> dict:
    """云服务 publicConfig（来自 cloud_config.json）。缺失时返回 null，页面退回本机保存。"""
    src = HERE / "cloud_config.json"
    if not src.exists():
        return {}
    try:
        return json.loads(src.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_cloud_sdk() -> str:
    """内联云 SDK（_vendor/cloud_sdk.js）。外链 jsdelivr 在国内基本连不上，
    登录按钮会静默失效，所以直接打包进 HTML。"""
    src = HERE / "_vendor" / "cloud_sdk.js"
    if not src.exists():
        return "window.__CLOUD_SDK_MISSING__=1;"
    js = src.read_text(encoding="utf-8")
    # 模板里已经包了一层 <script>，SDK 自身不能含闭合标签
    return js.replace("</script", "<\\/script")


def main() -> None:
    quiz = load_quiz()
    vocab = load_vocab()
    know = load_know()
    math = load_math()
    yanyu = load_yanyu()
    cloud = load_cloud()
    html = (TEMPLATE
            .replace("__QUIZ__", json.dumps(quiz, ensure_ascii=False, separators=(",", ":")))
            .replace("__VOCAB__", json.dumps(vocab, ensure_ascii=False, separators=(",", ":")))
            .replace("__KNOW__", json.dumps(know, ensure_ascii=False, separators=(",", ":")))
            .replace("__MATH__", json.dumps(math, ensure_ascii=False, separators=(",", ":")))
            .replace("__YANYU__", json.dumps(yanyu, ensure_ascii=False, separators=(",", ":")))
            .replace("__CLOUD_SDK__", load_cloud_sdk())
            .replace("__CLOUD__", json.dumps(cloud or None, ensure_ascii=False, separators=(",", ":"))))
    OUT.write_text(html, encoding="utf-8")

    # 线上部署包：只放入口页，不带题库源文件、备份目录。
    # 必须叫 index.html 且就是应用本体 —— WorkBuddy 登录回跳到站点根路径 '/'，
    # 若这里是跳转页，query 里的 code/state 会在 meta refresh 时丢掉。
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(html, encoding="utf-8")
    old = SITE / "app.html"
    if old.exists():
        old.unlink()

    # GitHub Pages 用 docs/ 发布（Pages 只认 root 或 /docs）。
    # 内容与 _site/index.html 完全一致，一份产物两处用。
    PAGES.mkdir(exist_ok=True)
    (PAGES / "index.html").write_text(html, encoding="utf-8")
    (PAGES / ".nojekyll").write_text("", encoding="utf-8")

    total = sum(len(p["questions"]) for p in quiz["papers"])
    print(f"OK  {len(quiz['papers'])} 期 / {total} 题 + {len(vocab)} 条成语 + {len(know)} 条知识点 "
          f"+ {len(math)} 道数量关系 + {len(yanyu)} 道言语理解 -> {OUT}")


if __name__ == "__main__":
    main()
