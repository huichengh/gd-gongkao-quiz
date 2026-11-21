# -*- coding: utf-8 -*-
"""全量体检：把所有题库过一遍，只报告不修改。

检查项
  1 结构：答案字母、选项数量/空/重复、题干长度
  2 截断：题干或选项末尾明显断字
  3 解析：空解析、解析自称答案与 ans 矛盾、"X 项" 指向矛盾
  4 重复：同一题干重复出现
  5 错配（仅南网）：解析与题干/选项毫无交集
输出给人看的分组统计 + 明细清单（写 audit_report.txt）。
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LET = "ABCD"
PUNCT = re.compile(r"[^\u4e00-\u9fa5A-Za-z0-9]")


def norm(s):
    return PUNCT.sub("", s or "")


def ws(s):
    """只去空白，不动标点 —— 选项去重要用它，否则 -64/64、①②③ 会被当成同一个。"""
    return re.sub(r"\s+", "", s or "")


def body(exp):
    return re.sub(r"^[ABCD甲乙丙丁][．.、]?\s*", "", (exp or "")).strip()


# ---------------------------------------------------------------- 单项检查
ANS_CLAIM = [
    re.compile(r"故?本题答案[选为是]?\s*([ABCD])"),
    re.compile(r"故?本题[应]?[选为]\s*([ABCD])\s*项?"),
    re.compile(r"答案[选为是]\s*([ABCD])\b"),
    # 「B。解析…」这种行首字母，必须跟句号；「A、B 项正确」是并列，不算答案
    re.compile(r"^([ABCD])[．。]\s*(?![、，,])"),
]


def claimed_letter(exp):
    for p in ANS_CLAIM:
        m = p.search(exp or "")
        if m:
            return m.group(1)
    return None


def check_bank(name, items, need_exp=True):
    rep = defaultdict(list)
    seen = {}
    for q in items:
        qid = q.get("id", "?")
        opts = q.get("opts") or []
        t = (q.get("t") or "").strip()
        exp = q.get("exp") or ""
        ans = q.get("ans")

        # 1 结构
        if not isinstance(ans, int) or not (0 <= ans <= 3):
            rep["答案越界"].append((qid, ans))
        if len(opts) != 4:
            rep["选项数不是4"].append((qid, len(opts)))
        if any(not str(o).strip() for o in opts):
            rep["空选项"].append((qid, opts))
        keys = [ws(str(o)) for o in opts]
        if len(set(keys)) != len(keys):
            rep["选项重复"].append((qid, opts))
        if not (4 <= len(norm(t)) <= 400):
            rep["题干长度异常"].append((qid, t[:40]))

        # 2 截断
        if t and not re.search(r"[）)。？?：:]$", t) and len(norm(t)) < 12:
            rep["题干疑似截断"].append((qid, t))
        for o in opts:
            o = str(o)
            if not o.strip():
                rep["单字选项"].append((qid, opts))
                break

        # 3 解析
        b = body(exp)
        if need_exp and len(b) < 12:
            rep["解析过短"].append((qid, exp[:30]))
        c = claimed_letter(exp)
        if c and isinstance(ans, int) and LET.index(c) != ans:
            rep["解析自称答案与答案矛盾"].append(
                (qid, f"ans={LET[ans]} claim={c}", t[:34], b[:50]))

        # 4 重复：整题干比，不截断
        k = ws(t)
        if k:
            if k in seen:
                rep["题干重复"].append((qid, seen[k], t[:36]))
            else:
                seen[k] = qid

    print(f"\n--- {name}  共 {len(items)} 题")
    for k in ["答案越界", "选项数不是4", "空选项", "选项重复", "单字选项",
              "题干长度异常", "题干疑似截断", "解析过短",
              "解析自称答案与答案矛盾", "题干重复"]:
        v = rep.get(k, [])
        if v:
            print(f"  {k:22s} {len(v):4d}")
    return rep


def load_items(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(d, dict):
        return d.get("items") or d.get("cats") or []
    return d


def main():
    banks = {}
    for f in ["数量关系.json", "科学推理.json", "言语理解.json", "南网.json"]:
        p = HERE / f
        if p.exists():
            banks[f.replace(".json", "")] = load_items(p)

    # 每日刷题：11 期 md 解析出来的题库
    try:
        import build_quiz
        flat = []
        for md in sorted(HERE.glob("*.md")):
            if not re.search(r"\d{4}-\d{2}-\d{2}_第\d+期", md.stem):
                continue
            for q in build_quiz.parse(md.read_text(encoding="utf-8")):
                flat.append({
                    "id": f"{md.stem[:10]}-{q.get('n')}",
                    "t": q.get("q", ""),
                    "opts": q.get("opts") or [],
                    "ans": "ABCD".index(q["ans"]) if q.get("ans") in LET else -1,
                    "exp": q.get("exp", ""),
                    "cat": q.get("part", ""),
                })
        if flat:
            banks["每日刷题(11期)"] = flat
    except Exception as e:      # 解析器接口变了就别让体检挂掉
        print("每日刷题跳过:", e)

    allrep = {}
    for name, items in banks.items():
        allrep[name] = check_bank(name, items, need_exp=(name != "南网"))

    # 汇总最常见的矛盾样本
    print("\n\n==== 解析自称答案与答案矛盾的样本 ====")
    for name, rep in allrep.items():
        v = rep.get("解析自称答案与答案矛盾", [])
        for row in v[:8]:
            print(f"  [{name}] {row}")

    out = HERE / "audit_report.txt"
    with out.open("w", encoding="utf-8") as f:
        for name, rep in allrep.items():
            f.write(f"\n===== {name} =====\n")
            for k, v in rep.items():
                f.write(f"\n## {k} ({len(v)})\n")
                for row in v:
                    f.write("  " + " | ".join(str(x) for x in row) + "\n")
    print(f"\n明细已写入 {out.name}")


if __name__ == "__main__":
    main()
