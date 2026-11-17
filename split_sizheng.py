#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把【四海】月度时政讲义解析成结构化素材：月份 → 主题 → 条目。

输入：_src2/*.txt（由 PDF 直出的纯文本，含 讲义 / 重点知识清单 / 补充材料）
输出：_src2/index_<MM>月.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "_src2"

NOISE = re.compile(
    r"(关注.{0,4}公众号|花生十三|每日图推|第\s*\d+\s*页|^\s*$|^\s*\d+\s*$)"
)
HEADING = re.compile(r"^([一二三四五六七八九十]{1,3})、\s*(.+)$")
ITEM = re.compile(r"^\s*(\d{1,3})[.．、]\s*(.*)$")
SECTION = re.compile(r"^【(知识清单|背诵清单|考点清单|本节练习)】")
# 出题价值高的信号
SIGNAL = re.compile(
    r"(\d+\s*年|\d+\s*月|\d+\s*日|百分之|%|万亿|亿元|万|亿|首次|首个|第一|唯一|最大|最高|最严|"
    r"目标|达到|建成|新增|覆盖|比例|规划|纲要|条例|办法|规定|部署|要求|强调|坚持|全面|"
    r"全会|会议|文件|讲话|公报|白皮书|报告)"
)


def clean_lines(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or NOISE.search(line):
            continue
        out.append(line)
    return out


def parse_file(path: Path) -> list[dict]:
    """返回 [{h: 标题, items: [条目...]}]"""
    lines = clean_lines(path.read_text(encoding="utf-8"))
    blocks: list[dict] = []
    cur = None
    in_list = False
    buf = ""
    num = None

    def flush():
        nonlocal buf, num, cur
        if cur is not None and buf.strip():
            cur["items"].append(re.sub(r"\s+", "", buf))
        buf, num = "", None

    for line in lines:
        m = HEADING.match(line)
        if m and len(line) <= 40:
            flush()
            if cur:
                blocks.append(cur)
            cur = {"h": f"{m.group(1)}、{re.sub(r'\\s+', '', m.group(2))}", "items": []}
            in_list = False
            continue
        sm = SECTION.match(line)
        if sm:
            flush()
            in_list = sm.group(1) == "知识清单"
            continue
        im = ITEM.match(line)
        if im and cur is not None:
            flush()
            if in_list:
                num = int(im.group(1))
                buf = im.group(2)
            continue
        if in_list and cur is not None:
            buf += line          # 续行拼接
    flush()
    if cur:
        blocks.append(cur)
    return [b for b in blocks if b["items"]]


def main() -> None:
    by_month: dict[str, list[dict]] = {}
    for p in sorted(SRC.glob("*.txt")):
        m = re.match(r"_(?:四海)?_?(\d{1,2})月", p.name) or re.search(r"(\d{1,2})月", p.name)
        if not m:
            key = "一号文件"
        else:
            key = f"{int(m.group(1)):02d}月"
        if "清单" not in p.name:
            # 讲义/补充材料里的知识清单结构与清单文件重复，只用来补标题
            pass
        by_month.setdefault(key, []).extend(parse_file(p))

    for key in sorted(by_month):
        blocks = by_month[key]
        # 同标题合并去重
        merged: dict[str, list[str]] = {}
        for b in blocks:
            merged.setdefault(b["h"], [])
            for it in b["items"]:
                if it not in merged[b["h"]]:
                    merged[b["h"]].append(it)

        total = sum(len(v) for v in merged.values())
        keep = 0
        seen = set()
        lines = [f"# {key} 时政素材（源自【四海】{key}讲义/清单，逐条摘录）", ""]
        for h, items in merged.items():
            picked = [it for it in items if SIGNAL.search(it)]
            if not picked:
                picked = items[:3]
            keep += len(picked)
            lines.append(f"## {h}")
            for it in picked:
                it = re.sub(r"^（[一二三四五六七八九十]+）", "", it).strip()
                if len(it) < 8 or re.fullmatch(r"[（(]?[一二三四五六七八九十\d]+[）)]?.{0,10}", it):
                    continue
                sig = re.sub(r"[，。、；：？！“”‘’（）()\s]", "", it)[:30]
                if sig in seen:
                    continue
                seen.add(sig)
                lines.append(f"- {it}")
            lines.append("")
        (SRC / f"index_{key}.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"{key}: 主题 {len(merged)}，条目 {total} → 保留 {keep}")

    # 一号文件单列
    print("\n一号文件单独处理")


if __name__ == "__main__":
    sys.exit(main())
