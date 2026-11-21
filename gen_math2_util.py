# -*- coding: utf-8 -*-
"""数量关系扩充题库的公共件：数值格式化、选项生成、答案校验。

每道题都写成 (答案, 干扰项, 算式) 三元组，算式必须算得和答案一模一样才入库。
网上流传的「真题答案」错得相当随意（同一页里答案与解析互相打架的都有），
所以这里不抄现成答案，只借题型。
"""
from fractions import Fraction as F
import hashlib


def fmt(v) -> str:
    """数字转选项文字：整数不带小数点，分数写成 a/b。"""
    if isinstance(v, F):
        if v.denominator == 1:
            return str(v.numerator)
        return f"{v.numerator}/{v.denominator}"
    f = float(v)
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f)))
    return ("%.4f" % f).rstrip("0").rstrip(".")


def _slot(qid: str) -> int:
    """用 id 的哈希定正确项落在第几个位置，保证同样输入永远同样输出。"""
    return int(hashlib.md5(qid.encode()).hexdigest(), 16) % 4


def build(rows):
    """rows: (id, cat, tag, lv, 题干, 单位, 答案, [干扰1..3], 解析, 算式)

    返回条目列表；任何一处对不上就抛 AssertionError，不会写进题库。
    """
    items = []
    for (qid, cat, tag, lv, stem, unit, ans, wrongs, exp, solver) in rows:
        got = solver()
        assert abs(float(got) - float(ans)) < 1e-9, (
            f"{qid} 算式与标注答案不一致：算得 {float(got)}，标的是 {float(ans)}")
        assert len(wrongs) == 3, f"{qid} 干扰项必须 3 个"
        texts = [fmt(ans)] + [fmt(w) for w in wrongs]
        texts = [t + unit for t in texts]
        assert len(set(texts)) == 4, f"{qid} 选项重复：{texts}"
        assert all(t.strip() for t in texts), f"{qid} 有空选项"

        k = _slot(qid)
        rest = texts[1:]
        opts = rest[:k] + [texts[0]] + rest[k:]
        items.append({
            "id": qid, "tag": tag, "lv": lv, "t": stem,
            "opts": opts, "ans": k, "exp": exp, "cat": cat,
        })
    return items
