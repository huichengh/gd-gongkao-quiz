# -*- coding: utf-8 -*-
"""按解析里的判断句反推答案，与标注答案比对，输出待复核清单。

原理：解析里如果写了「B 项正确」「C 项错误」「A 不符合题意」这类判断，
单选/选非题的答案就能被反推出来。反推结果与标注 answers 不一致的，
要么答案错了，要么解析配错了题，都值得人工看一眼。
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LET = "ABCD"

# 「B 项正确」「C项错误」「A 符合题意」「D 当选」「A 选项说法错误」
EVAL = re.compile(
    r"([ABCD])\s*(?:项|选项)?\s*(正确|错误|符合题意|不符合题意|当选|不选|说法正确|说法错误)"
)
# 并列写法：「A、B 项正确」「A、B、C 三项均正确」「BC 说法正确」
EVAL_LIST = re.compile(
    r"([ABCD](?:\s*[、,，]\s*[ABCD]){1,3})\s*(?:选项|项|三项|两项|等)?\s*"
    r"(均|都)?\s*(正确|错误|符合题意|不符合题意|当选|不选|说法正确|说法错误)"
)
EVAL2 = re.compile(r"(?<![A-Za-z])([ABCD])\s*(正确|错误)(?=[，,。；;、])")

NEG_STEM = re.compile(r"不正确|错误|不包括|不属于|除外|不符合|不恰当|有误|不能")


def evals(exp):
    """抽出解析里对选项的判断，返回 {字母: 极性}，极性 1=对 0=错。"""
    out = {}

    def put(letter, good):
        if letter in out and out[letter] != good:
            return                 # 同一项被夸又被打，忽略
        out[letter] = 1 if good else 0

    for m in EVAL_LIST.finditer(exp):
        letters = re.findall(r"[ABCD]", m.group(1))
        good = m.group(3) in ("正确", "符合题意", "当选", "说法正确")
        for L in letters:
            put(L, good)

    for p in (EVAL, EVAL2):
        for m in p.finditer(exp):
            put(m.group(1), m.group(2) in ("正确", "符合题意", "当选", "说法正确"))
    return out


def infer(ev, neg):
    """由判断句反推答案下标。只认「四个选项都评价过」的情形——少评一项就可能
    把「解析没提到的那个」误当答案（例如「C 说法正确但不体现题意」，答案其实是
    B），所以宁可少判也不误判。"""
    if len(ev) < 4:
        return None
    good = [k for k, v in ev.items() if v == 1]
    bad = [k for k, v in ev.items() if v == 0]
    if neg:
        return LET.index(bad[0]) if len(bad) == 1 else None
    return LET.index(good[0]) if len(good) == 1 else None


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d["items"] if isinstance(d, dict) else d


def run(name, items):
    flags, stats = [], Counter()
    for q in items:
        t = q.get("t") or ""
        exp = q.get("exp") or ""
        ans = q.get("ans")
        if not isinstance(ans, int) or ans < 0:
            continue
        ev = evals(exp)
        if not ev:
            stats["解析里没有判断句"] += 1
            continue
        got = infer(ev, bool(NEG_STEM.search(t)))
        if got is None:
            stats["判断句推不出唯一答案"] += 1
            continue
        stats["可反推"] += 1
        if got != ans:
            flags.append({
                "id": q.get("id", "?"), "cat": q.get("cat", ""),
                "t": t[:60], "ans": LET[ans], "infer": LET[got],
                "ev": {k: ("对" if v else "错") for k, v in ev.items()},
                "exp": exp[:120],
            })
    print(f"\n--- {name}  {len(items)} 题")
    for k, v in stats.most_common():
        print(f"    {k:18s} {v:5d}")
    print(f"    反推与标注矛盾       {len(flags):5d}")
    return flags


def main():
    banks = []
    for f in ["数量关系.json", "科学推理.json", "言语理解.json", "南网.json"]:
        p = HERE / f
        if p.exists():
            banks.append((f.replace(".json", ""), load(p)))

    allf = {}
    for name, items in banks:
        allf[name] = run(name, items)

    total = sum(len(v) for v in allf.values())
    print(f"\n==== 合计待复核 {total} 条 ====")
    with (HERE / "calib_candidates.json").open("w", encoding="utf-8") as f:
        json.dump(allf, f, ensure_ascii=False, indent=1)
    for name, v in allf.items():
        if v:
            print(f"\n## {name} ({len(v)})")
            for x in v[:10]:
                print(f"  {x['id']} 标答案={x['ans']} 反推={x['infer']} {x['ev']} | {x['t']}")


if __name__ == "__main__":
    main()
