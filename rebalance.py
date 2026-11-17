#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打散题库答案分布：把正确项在 A/B/C/D 之间的位置调到大致均匀。

只做"选项位置交换"，不改题干、不改正确内容、不改解析。
带数字、年份、"第X"、"以上"等有序语义的题目一律不动，
避免出现"A. 第二　B. 第三　C. 第一"这类别扭的排列。

用法：python rebalance.py <题库.md> [--dry]
"""
import re
import sys
import pathlib
from collections import Counter

path = pathlib.Path(sys.argv[1])
dry = "--dry" in sys.argv
raw = path.read_text(encoding="utf-8")
lines = raw.split("\n")

qblocks = {}
cur = None
for i, line in enumerate(lines):
    s = line.strip()
    m = re.match(r"^\*\*(\d+)\.\*\*\s*(.+)$", s)
    if m:
        cur = int(m.group(1))
        qblocks[cur] = {"q": m.group(2), "opts": {}}
        continue
    m = re.match(r"^([A-D])\.\s*(.+)$", s)
    if m and cur is not None:
        qblocks[cur]["opts"][m.group(1)] = (i, m.group(2))

anslines = {}
exp_text = {}
for i, line in enumerate(lines):
    s = line.strip()
    m = re.match(r"^\*\*(\d+)\.\s*([A-D])\*\*\s*(.*)$", s)
    if m:
        n = int(m.group(1))
        anslines[n] = (i, m.group(2))
        exp_text[n] = m.group(3)

ORDERED = re.compile(r"[0-9０-９]|第[一二三四五六七八九十]|以上|均|都")


def is_ordered(opts):
    return any(ORDERED.search(t) for _, t in opts.values())


def refs_letter(n):
    # 解析里若出现"B 项"这类字母引用，交换后会指错，直接跳过
    return bool(re.search(r"(?<![A-Za-z])[A-D]\s*项", exp_text.get(n, "")))


def eligible(n):
    b = qblocks.get(n)
    if not b or len(b["opts"]) != 4 or n not in anslines:
        return False
    if is_ordered(b["opts"]):
        return False
    if refs_letter(n):
        return False
    return True


counts = Counter(a for _, a in anslines.values())
total = len(anslines)
target = total // 4
print("原分布:", dict(counts), "｜目标每题数:", target)

need = {L: target - counts[L] for L in "ABCD"}   # 正=缺，负=多
pool = {L: [n for n in anslines if anslines[n][1] == L and eligible(n)] for L in "ABCD"}
for L in "ABCD":
    pool[L].sort()

moved = []
for L in "ABCD":
    while need[L] < 0 and pool[L]:
        # 优先迁往缺得最多的字母
        to = max("ABCD", key=lambda x: need[x])
        if need[to] <= 0:
            break
        n = pool[L].pop()
        i1, t1 = qblocks[n]["opts"][L]
        i2, t2 = qblocks[n]["opts"][to]
        if dry:
            moved.append((n, L, to))
        else:
            lines[i1] = f"{L}. {t2}"
            lines[i2] = f"{to}. {t1}"
            ai, old = anslines[n]
            lines[ai] = lines[ai].replace(f"**{n}. {old}**", f"**{n}. {to}**", 1)
            anslines[n] = (ai, to)
            qblocks[n]["opts"][L] = (i1, t2)
            qblocks[n]["opts"][to] = (i2, t1)
        need[L] += 1
        need[to] -= 1
        moved.append((n, L, to))

print(f"调整 {len(moved)} 题，其中可重排题总数 {sum(len(v) for v in pool.values()) + len(moved)}")

if not dry:
    path.write_text("\n".join(lines), encoding="utf-8")
    final = Counter(a for _, a in anslines.values())
    print("新分布:", dict(final))
else:
    print("dry-run，未写入")

# 仍有序但答案集中的题，提示一下（不处理）
rest = [n for n in anslines if not eligible(n)]
print(f"因有序语义/字母引用而保留原位的题：{len(rest)} 道")
