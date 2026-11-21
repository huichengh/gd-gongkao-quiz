# -*- coding: utf-8 -*-
"""生成《科学推理.json》。

广东科学推理的题全部来自初中理化生地的常识与定性推理，
网上流传的「真题」大多没有官方答案，所以这里不抄题，
按考纲考点自己出，每题给可核验的解析。

答案位置用 id 的哈希打散，避免全部堆在 A。
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

from gen_sci_phys import phys_items
from gen_sci_other import sci_items

OUT = Path(__file__).resolve().parent / "科学推理.json"

CATS = ["物理·力学", "物理·电学", "物理·光声热", "化学", "生物", "地理"]


def slot(qid: str) -> int:
    return int(hashlib.md5(qid.encode()).hexdigest(), 16) % 4


def balance(items: list) -> None:
    """把正确项在 A/B/C/D 之间摊匀：只交换选项位置，不改内容。"""
    for _ in range(20000):
        cnt = Counter(it["ans"] for it in items)
        counts = [cnt.get(k, 0) for k in range(4)]
        hi = max(range(4), key=lambda k: counts[k])
        lo = min(range(4), key=lambda k: counts[k])
        if counts[hi] - counts[lo] <= 1:
            break
        donor = next((it for it in items if it["ans"] == hi), None)
        if donor is None:
            break
        donor["opts"][hi], donor["opts"][lo] = donor["opts"][lo], donor["opts"][hi]
        donor["ans"] = lo


def main() -> None:
    rows = phys_items() + sci_items()
    items = []
    seen = set()
    for (qid, cat, tag, lv, stem, opts, ans, exp) in rows:
        assert qid not in seen, f"id 重复：{qid}"
        seen.add(qid)
        assert qid.startswith("s"), f"{qid} 科学推理的 id 应以 s 开头（避免和数量关系撞）"
        assert cat in CATS, f"{qid} 分类不认识：{cat}"
        assert len(opts) == 4, f"{qid} 选项不是 4 个"
        assert len(set(opts)) == 4, f"{qid} 选项重复：{opts}"
        assert all(o.strip() for o in opts), f"{qid} 有空选项"
        assert 0 <= ans < 4, f"{qid} 答案下标越界"
        assert len(exp) > 12, f"{qid} 解析太短，等于没讲"

        k = slot(qid)
        opts2 = list(opts)
        opts2[0], opts2[k] = opts2[k], opts2[0]
        items.append({
            "id": qid, "tag": tag, "lv": lv, "t": stem,
            "opts": opts2, "ans": k, "exp": exp, "cat": cat,
        })

    balance(items)
    cnt = Counter(it["ans"] for it in items)
    print("答案分布:", {("ABCD"[k]): cnt.get(k, 0) for k in range(4)})
    print("分类:", {c: sum(1 for x in items if x["cat"] == c) for c in CATS})

    doc = {"updated": "2026-11-21", "topic": "物理 / 化学 / 生物 / 地理", "items": items}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK  {len(items)} 道 -> {OUT}")


if __name__ == "__main__":
    main()
