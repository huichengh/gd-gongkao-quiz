#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把《时政素材_2026.md》里讲义内部的子标题从 ## 降为 ###。

讲义原文里像《城市更新"十五五"规划》《加快农业农村现代化"十五五"规划》
这类文件自带"一、总体要求"式的内部编号，抽取时混进了 ## 层级，
看起来像新开了一个时政事件。规则：同一个月段内，编号不是严格递增的
## 标题，判为子标题，降为 ###。
"""
import re
import sys
from pathlib import Path

CN = "一二三四五六七八九十"
ORD = re.compile(r"^##\s+([一二三四五六七八九十百]+)、")


def num(s):
    """把中文数字（一—九十九）转成 int，失败返回 0。"""
    if s == "十":
        return 10
    if "十" in s:
        a, _, b = s.partition("十")
        return (CN.index(a) + 1 if a else 1) * 10 + (CN.index(b) + 1 if b else 0)
    if len(s) == 1 and s in CN:
        return CN.index(s) + 1
    return 0


def main(path):
    p = Path(path)
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    month = None
    seen_max = 0
    demoted = 0
    for ln in lines:
        if ln.startswith("## 【"):
            month = ln[3:8]
            seen_max = 0
            out.append(ln)
            continue
        m = ORD.match(ln)
        if m:
            n = num(m.group(1))
            if n and n <= seen_max:
                out.append("###" + ln[2:])
                demoted += 1
                continue
            if n:
                seen_max = n
        out.append(ln)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("降级子标题", demoted, "条；总行数", len(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "时政素材_2026.md")
