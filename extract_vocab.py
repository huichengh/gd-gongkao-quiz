#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从《高频800词记忆版》PDF 提取 词条 + 释义。

PDF 为图片型（无文字层）：渲染 200dpi → RapidOCR → 用表格网格线（横线切行、竖线切列）还原单元格。
输出 _vocab/items.json：[{w 词条, d 释义, g 组, s 小类, p 页码, conf 置信度}]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

HERE = Path(__file__).resolve().parent
OUT = HERE / "_vocab"
PDF = r"C:/Users/84307/Desktop/高频800词记忆版--（白色底图）.pdf"
DPI = 200


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    hits = np.where(mask)[0]
    if len(hits) == 0:
        return []
    groups, s, p = [], hits[0], hits[0]
    for y in hits[1:]:
        if y - p <= 2:
            p = y
        else:
            groups.append((int(s), int(p)))
            s = p = y
    groups.append((int(s), int(p)))
    return groups


def grid(img_path: Path):
    """返回 (横线 y 列表, 竖线 x 列表)。必须先把画面裁到表格范围，否则白边会把占比摊薄。"""
    a = np.array(Image.open(img_path).convert("L"))
    h, w = a.shape
    x0, x1 = max(0, int(w * 0.07)), min(w, int(w * 0.96))
    y0, y1 = max(0, int(h * 0.03)), min(h, int(h * 0.97))
    sub = a[y0:y1, x0:x1]
    hl = [int((s + e) / 2) + y0 for s, e in _runs((sub < 170).mean(axis=1) > 0.60) if e - s <= 4]
    # 竖线只在表格纵向范围内统计：表格没铺满整页时，全页比例会被白边摊薄到检不出来
    if hl:
        ty0 = max(0, hl[0] - 6)
        ty1 = min(h, hl[-1] + 6)
        band = a[ty0:ty1, x0:x1]
        vl = [int((s + e) / 2) + x0 for s, e in _runs((band < 170).mean(axis=0) > 0.55) if e - s <= 6]
    else:
        vl = []
    return hl, vl


def norm(t: str) -> str:
    return re.sub(r"\s+", "", t or "")


def page_items(args) -> tuple[int, list[dict]]:
    """处理单页，返回 [(页号, 条目)]，供多进程调用"""
    pno, pdf_path = args
    doc = pymupdf.open(pdf_path)
    page = doc[pno]
    png = OUT / f"_p{pno:02d}.png"
    if not png.exists():
        page.get_pixmap(dpi=DPI).save(png)
    doc.close()

    hl, vl = grid(png)
    if len(hl) < 3 or len(vl) < 4:
        return pno, []

    cols = [(vl[i], vl[i + 1]) for i in range(len(vl) - 1)]
    widths = [b - a for a, b in cols]
    expl_i = int(np.argmax(widths))
    word_i = max(0, expl_i - 1)
    wx0, wx1 = cols[word_i]
    ex0, ex1 = cols[expl_i]

    ocr = RapidOCR()
    res, _ = ocr(str(png))
    blocks = []
    for b in res or []:
        t = norm(b[1])
        if not t:
            continue
        xs = [q[0] for q in b[0]]
        ys = [q[1] for q in b[0]]
        blocks.append({
            "y": sum(ys) / 4,
            "x0": min(xs), "x1": max(xs),
            "cx": (min(xs) + max(xs)) / 2,
            "t": t,
            "sc": float(b[2]) if len(b) > 2 else 1.0,
        })

    group = ""
    for b in sorted(blocks, key=lambda x: x["y"]):
        if b["cx"] < wx0 and b["t"].startswith("【第"):
            group = b["t"]

    bands = list(zip(hl[:-1], hl[1:])) + [(hl[-1], 10 ** 6)]
    cells = [{"w": [], "d": [], "s": []} for _ in bands]

    for b in blocks:
        ri = None
        for i, (y0, y1) in enumerate(bands):
            if y0 <= b["y"] < y1:
                ri = i
                break
        if ri is None:
            continue
        if wx0 - 4 <= b["cx"] <= wx1 + 4 and len(b["t"]) <= 12:
            cells[ri]["w"].append(b)
        elif ex0 - 8 <= b["cx"] <= ex1 + 80:
            cells[ri]["d"].append(b)
        elif b["cx"] < wx0 and len(b["t"]) <= 12:
            cells[ri]["s"].append(b)

    out: list[dict] = []
    subcat = ""
    carry: list[dict] = []
    for c in cells:
        if c["s"]:
            subcat = c["s"][0]["t"]
        if not c["w"]:
            if c["d"]:
                carry.extend(c["d"])
            continue
        for wb in sorted(c["w"], key=lambda x: x["y"]):
            seg = sorted(c["d"] + carry, key=lambda e: (round(e["y"] / 8), e["x0"]))
            carry = []
            text = norm("".join(e["t"] for e in seg))
            word = wb["t"]
            if word in ("成语", "词语", "词组", "解释") or text.startswith("解释"):
                continue
            out.append({
                "w": word, "d": text, "g": group, "s": subcat, "p": pno + 1,
                "conf": round(min([wb["sc"]] + [e["sc"] for e in seg]), 3),
            })
    return pno, out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    argv = sys.argv[1:]
    chunk = None
    total = pymupdf.open(PDF).page_count
    if len(argv) == 2:
        chunk = (int(argv[0]), int(argv[1]))
        lo, hi = chunk
    else:
        lo, hi = 0, total

    results = []
    for i in range(lo, min(hi, total)):
        pno, rows = page_items((i, PDF))
        results.append((pno, rows))
        print(f"p{pno+1:02d}: {len(rows)} 条", flush=True)

    items: list[dict] = []
    for pno, rows in sorted(results):
        items.extend(rows)

    if chunk:
        out_path = OUT / f"part_{chunk[0]:02d}_{chunk[1]:02d}.json"
        out_path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        print(f"chunk {chunk} -> {out_path.name}  {len(items)} 条", flush=True)
        return

    best: dict[str, dict] = {}
    for r in items:
        k = r["w"]
        if k not in best or len(r["d"]) > len(best[k]["d"]):
            best[k] = r
    out = list(best.values())
    (OUT / "items.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    empty = [r for r in out if len(r["d"]) < 6]
    odd = [r for r in out if not re.fullmatch(r"[\u4e00-\u9fa5]{2,8}", r["w"])]
    low = [r for r in out if r["conf"] < 0.85]
    print(f"\n去重后 {len(out)} 条；释义为空 {len(empty)}；词形异常 {len(odd)}；低置信 {len(low)}")
    for r in (empty + odd)[:20]:
        print(f"  p{r['p']:>2} 「{r['w']}」｜{r['d'][:40]}")


if __name__ == "__main__":
    sys.exit(main())
