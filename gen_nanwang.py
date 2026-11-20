# -*- coding: utf-8 -*-
"""南方电网题库提取器 -> 南网.json

只服务「南方电网」这一个模块，数据不与其他模块共用。

支持两种排版：
  A 中公系：  "12.题干（　）。" / "A.选项" / 答案侧 "12.【答案】C。解析：…"
  B 企业文化："12．题干" / "A。选项" / 同一文件内 "答案：C"

对齐：讲义与答案是两份文件时，按题号序列做 LCS 对齐，自动跳过两边各自缺的题。
"""
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import pymupdf

SRC = Path(r"C:/Users/84307/Desktop/南网中公")
OUT = Path(__file__).resolve().parent / "南网.json"

NOISE_EXACT = {
    "内部资料", "免费交流", "内部资料 免费交流", "内部资料·免费交流",
    "报名专线：400-6300-999", "报名专线:400-6300-999",
}
NOISE_SUB = ("内部资料", "免费交流", "报名专线", "400-6300-999", "baizhizhan")

OP_A = re.compile(r"^\s*([A-D])\s*[.．、]\s*(.*)$")
OP_B = re.compile(r"^\s*([A-D])\s*[。．.]\s*(.*)$")
NUM_A = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*(.*)$")
ANS_A = re.compile(r"^\s*(\d{1,3})\s*[.．、]?\s*【答案】\s*([ABCD]{1,4})")
ANS_B = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*(.*?)\s*[。.]?\s*答案\s*[：:]\s*([ABCD])")
ANS_B2 = re.compile(r"^\s*答案\s*[：:]\s*([ABCD])")


def page_lines(path: Path) -> list[str]:
    doc = pymupdf.open(path)
    out = []
    for page in doc:
        for raw in page.get_text().splitlines():
            s = raw.strip()
            if not s or s in NOISE_EXACT:
                continue
            if any(n in s for n in NOISE_SUB):
                continue
            if re.fullmatch(r"[0-9IVXLC]{1,4}", s):
                continue
            out.append(s)
    text = "\n".join(out)
    text = re.sub(r"（\s*\n\s*）", "（　）", text)
    text = re.sub(r"\(\s*\n\s*\)", "（　）", text)
    text = re.sub(r"（\s*）", "（　）", text)
    return text.splitlines()


CHAP = re.compile(r"^第[一二三四五六七八九十百]+\s*[章节]")


def is_chapter(s: str) -> bool:
    return bool(CHAP.match(s)) and len(s) <= 30


def is_heading(s: str) -> bool:
    if not (2 <= len(s) <= 40):
        return False
    if OP_A.match(s) or NUM_A.match(s):
        return False
    if any(ch in s for ch in "。；：，？!?："):
        return False
    if "【答案】" in s or "解析" in s or "答案" in s:
        return False
    return True


def parse_questions(path: Path) -> list[dict]:
    """讲义侧：以「连续 4 个 A/B/C/D 选项」为锚点，向上回溯找题号与题干。

    法律、公文这类资料把知识点和题目混排，两者的编号都是「1.」，只靠编号
    无法区分，所以改为以选项组反推题干。
    """
    lines = page_lines(path)
    n = len(lines)
    qs, head, idx = [], "", 0
    while idx < n:
        s = lines[idx]
        if is_chapter(s):
            head = s
        if not OP_A.match(s):
            idx += 1
            continue
        # 收四个连续选项，中间允许夹续行
        opts, j = [], idx
        while j < n and len(opts) < 4:
            m = OP_A.match(lines[j])
            if m:
                if m.group(1) != "ABCD"[len(opts)]:
                    break
                opts.append(m.group(2).strip())
                j += 1
            elif opts:
                opts[-1] += lines[j].strip()
                j += 1
            else:
                break
        if len(opts) < 4:
            idx += 1
            continue
        # 回溯：最近的题号行即题干
        num, stem, k = 0, "", idx - 1
        while k >= 0:
            m = NUM_A.match(lines[k])
            if m:
                num, stem = int(m.group(1)), m.group(2).strip()
                break
            if is_heading(lines[k]):
                break
            k -= 1
        if stem:
            qs.append({"head": head, "num": num, "stem": stem, "opts": [
                ("ABCD"[i], v) for i, v in enumerate(opts)]})
        idx = j
    return qs


def parse_answers(path: Path) -> list[dict]:
    """答案侧：抽题号 + 答案 + 解析。"""
    lines = page_lines(path)
    out, head, i = [], "", 0
    while i < len(lines):
        s = lines[i]
        m = ANS_A.match(s)
        if m:
            num, letter = int(m.group(1)), m.group(2)
            multi = len(letter) > 1        # 多选先占位，配对后再丢，避免序列缺号
            body = [s[s.find("】") + 1:].lstrip("。 ").replace("解析：", "").strip()]
            j = i + 1
            while j < len(lines):
                t = lines[j]
                if ANS_A.match(t) or NUM_A.match(t) or is_heading(t):
                    break
                body.append(t)
                j += 1
            out.append({"head": head, "num": num, "ans": letter[0], "multi": multi,
                        "exp": "".join(body).strip()})
            i = j
            continue
        if is_heading(s):
            if is_chapter(s):
                head = s
        i += 1
    return out


def lcs_pair(qs: list[dict], ans: list[dict]) -> list[tuple[dict, dict]]:
    qn = [q["num"] for q in qs]
    an = [a["num"] for a in ans]
    sm = SequenceMatcher(None, qn, an, autojunk=False)
    hit = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                hit.append((qs[i1 + k], ans[j1 + k]))
    return hit


# ---------------------------------------------------------------- 质量闸门
def ok(q: dict, a: dict) -> bool:
    stem = q["stem"].strip()
    opts = [o[1].strip() for o in q["opts"]]
    if not (6 <= len(stem) <= 160):
        return False
    if any(len(o) < 1 or len(o) > 70 for o in opts):
        return False
    if len(set(opts)) != 4:
        return False
    # 题干里知识点残留：出现「概念：」「是指」且在开头，视为污染
    if re.match(r"^(概念|定义)[：:]", stem):
        return False
    if stem.count("（）") or stem.count("(  )") :
        pass
    if a["ans"] not in "ABCD":
        return False
    return True


def build(cat: str, tag: str, qf: Path, af: Path | None) -> list[dict]:
    qs = parse_questions(qf)
    if af is None:
        return []
    if not af.exists():
        return []
    ans = parse_answers(af)
    pairs = lcs_pair(qs, ans)
    items = []
    for q, a in pairs:
        if a.get("multi"):
            continue
        if not ok(q, a):
            continue
        stem = re.sub(r"^[（(]\s*(单选|多选|判断|不定项)[^）)]*[）)]\s*", "", q["stem"].strip())
        items.append({
            "cat": cat,
            "tag": q["head"] or tag,
            "t": stem,
            "opts": [o[1].strip().rstrip("，,") for o in q["opts"]],
            "ans": "ABCD".index(a["ans"]),
            "exp": a["exp"].strip(),
        })
    return items


def build_wenhua() -> list[dict]:
    """企业文化题库：题干 / A。选项 / 答案：X 都在同一份 PDF 里。"""
    f = SRC / "资料/4-【南方电网】企业文化/南方电网企业文化/南方电网招聘企业文化题库.pdf"
    if not f.exists():
        return []
    lines = page_lines(f)
    items, cur = [], None
    for s in lines:
        m_num = re.match(r"^\s*(\d{1,3})\s*[．.、]\s*(.+)$", s)
        m_op = OP_B.match(s)
        m_ans = ANS_B2.match(s)
        if m_ans and cur is not None and len(cur["opts"]) == 4:
            cur["ans"] = m_ans.group(1)
            if all(k in cur for k in ("stem", "opts", "ans")):
                items.append(cur)
            cur = None
            continue
        if m_op and cur is not None and len(cur["opts"]) < 4:
            cur["opts"].append(m_op.group(2).strip())
            continue
        if m_num and (cur is None or len(cur.get("opts", [])) >= 2):
            if cur and len(cur.get("opts", [])) == 4 and "ans" in cur:
                items.append(cur)
            cur = {"stem": m_num.group(2).strip(), "opts": []}
            continue
        if cur is not None and not cur["opts"]:
            cur["stem"] += s
    out = []
    for it in items:
        if len(it["opts"]) != 4 or "ans" not in it:
            continue
        stem = re.sub(r"\s+", "", it["stem"])
        if not (6 <= len(stem) <= 160):
            continue
        out.append({
            "cat": "企业文化", "tag": "南方电网企业文化",
            "t": stem,
            "opts": [re.sub(r"\s+", "", o) for o in it["opts"]],
            "ans": "ABCD".index(it["ans"]),
            "exp": "",
        })
    return out


SOURCES = [
    ("管理学", "管理", "管理/管理.pdf", "管理/管理答案.pdf"),
    ("经济学", "微观宏观经济学", "经济/经济学.pdf", "经济/经济学答案.pdf"),
    ("经济学", "微观宏观经济学", "经济/经济学2.pdf", "经济/经济学答案2.pdf"),
    ("马克思主义", "马克思主义基本原理", "马克思/马克思主义基本原理练题班.pdf",
     "马克思/马克思主义基本原理练题班答案及解析.pdf"),
    ("计算机基础", "计算机基础", "计算机基础/计算机基础题库-讲义.pdf", "计算机基础/计算机基础题库-答案.pdf"),
    ("计算机基础", "计算机基础", "计算机基础/计算机基础-讲义.pdf", "计算机基础/计算机基础-答案.pdf"),
    ("计算机基础", "Office 办公", "计算机基础/office-讲义.pdf", "计算机基础/office-答案.pdf"),
    ("公文写作", "公文写作与处理", "公文/公文写作与处理讲义与答案.pdf",
     "公文/公文写作与处理讲义与答案.pdf"),
    ("法律", "民法", "法律/民法.pdf", "法律/民法答案.pdf"),
    ("法律", "刑法", "法律/刑法.pdf", "法律/刑法答案.pdf"),
    ("法律", "宪法", "法律/宪法.pdf", "法律/宪法答案.pdf"),
    ("法律", "法理学", "法律/法理学.pdf", "法律/法理学答案.pdf"),
]


def main() -> None:
    allitems = []
    for cat, tag, qf, af in SOURCES:
        qp, ap = SRC / qf, SRC / af
        if not qp.exists():
            print(f"  跳过（无讲义）{qf}")
            continue
        if not ap.exists():
            print(f"  跳过（无答案）{af}")
            continue
        items = build(cat, tag, qp, ap)
        print(f"  {cat:6s} {Path(qf).stem:22s} {len(items):4d} 题")
        allitems.extend(items)

    wh = build_wenhua()
    print(f"  {'企业文化':6s} {'企业文化题库':22s} {len(wh):4d} 题")
    allitems.extend(wh)

    # 去重：题干前 24 字相同视为重复
    seen, uniq = set(), []
    for it in allitems:
        key = re.sub(r"\s+", "", it["t"])[:24]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)

    for i, it in enumerate(uniq, 1):
        it["id"] = "n%04d" % i

    print("\n合计", len(allitems), "去重后", len(uniq))
    print("科目分布", dict(Counter(x["cat"] for x in uniq)))
    print("答案分布", dict(Counter(x["ans"] for x in uniq)))

    doc = {"updated": "2026-11-20", "topic": "南方电网笔试", "items": uniq}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写入", OUT.name, OUT.stat().st_size, "字节")


if __name__ == "__main__":
    main()
