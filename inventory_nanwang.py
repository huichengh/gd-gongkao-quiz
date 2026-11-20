# -*- coding: utf-8 -*-
"""盘点：南网中公资料里到底有多少题，哪些还没进 南网.json。

只读，不改任何数据。输出 inventory.json + 控制台摘要。
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

SRC = Path(r"C:/Users/84307/Desktop/南网中公")
OUT = Path(__file__).resolve().parent / "inventory.json"

ANS_A = re.compile(r"【答案】\s*([ABCD]{1,4})")
ANS_B = re.compile(r"答案\s*[：:]\s*([ABCD])")
ANS_C = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*([ABCD])\s*$")     # 答题卡式 "12. B"
OP = re.compile(r"^\s*([A-D])\s*[.．、。]\s*\S")
NUMQ = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*\S")


def analyze(path: Path) -> dict:
    info = {"path": str(path.relative_to(SRC)), "ext": path.suffix.lower()}
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        info["error"] = str(e)[:80]
        return info
    info["pages"] = doc.page_count
    text = []
    for page in doc:
        text.append(page.get_text())
    doc.close()
    txt = "\n".join(text)
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    info["chars"] = len(txt)
    info["ans_mark"] = len(ANS_A.findall(txt)) + len(ANS_B.findall(txt))
    info["opt_lines"] = sum(1 for l in lines if OP.match(l))
    info["q_lines"] = sum(1 for l in lines if NUMQ.match(l))
    info["est_q"] = info["opt_lines"] // 4
    info["scanned"] = info["chars"] < 200
    return info


def main():
    files = sorted([p for p in SRC.rglob("*") if p.suffix.lower() in (".pdf", ".doc", ".docx")])
    print(f"待扫描 {len(files)} 个文件")
    rows = []
    for i, p in enumerate(files, 1):
        if p.suffix.lower() != ".pdf":
            rows.append({"path": str(p.relative_to(SRC)), "ext": p.suffix.lower(), "note": "非 PDF，未解析"})
            continue
        rows.append(analyze(p))
        if i % 50 == 0:
            print(f"  {i}/{len(files)}")
            sys.stdout.flush()
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    q = [r for r in rows if r.get("est_q", 0) >= 3]
    q.sort(key=lambda r: -r["est_q"])
    print(f"\n疑似含题（选项组≥3 组）的文件 {len(q)} 个，估算总题量 {sum(r['est_q'] for r in q)}")
    print(f"{'估算题量':>8}  {'答案标记':>6}  {'页':>4}  文件")
    for r in q[:40]:
        print(f"{r['est_q']:>8}  {r['ans_mark']:>6}  {r.get('pages',0):>4}  {r['path']}")

    bad = [r for r in rows if r.get("scanned")]
    print(f"\n疑似扫描件（几乎无文字层）{len(bad)} 个")
    for r in bad[:15]:
        print("   ", r["path"])

    nd = [r for r in rows if r["ext"] in (".doc", ".docx")]
    print(f"\n非 PDF（无法用 pymupdf 解析）{len(nd)} 个")
    for r in nd:
        print("   ", r["path"])


if __name__ == "__main__":
    main()
