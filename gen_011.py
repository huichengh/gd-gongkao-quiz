# -*- coding: utf-8 -*-
# 第 011 期（2026-11-24）生成器
# 主板块 C5（2026 年 8 月）；副板块 C18（8 月健康中国与防灾）
# 阶次：二阶 · 反向辨析（不属于 / 错误的是 / 提法归属）
import importlib.util
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LET = 'ABCD'


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ITEMS


P1 = load('p011_p1')
P2 = load('p011_p2')
P3 = load('p011_p3')
P4 = load('p011_p4')

CKS = P1 + P2
ZZ = P3 + P4

assert len(P1) == 50, len(P1)
assert len(P2) == 50, len(P2)
assert len(P3) == 50, len(P3)
assert len(P4) == 50, len(P4)
assert len(CKS) == 100 and len(ZZ) == 100

for it in CKS + ZZ:
    s, o, a, k, e = it
    assert len(o) == 4, s
    assert len(set(o)) == 4, s
    assert 0 <= a <= 3, s
    assert k.strip() and e.strip(), s

DIGIT = re.compile(r'[0-9０-９]')
NUMONLY = re.compile(r'^[0-9]+(?:\.[0-9]+)?\s*[^0-9]{0,12}$')


def scatter(items):
    """把正确项均匀分布到 A/B/C/D；纯数字选项之间不互换，避免时序被打乱。"""
    need = {i: len(items) // 4 for i in range(4)}
    out = []
    for s, o, a, k, e in items:
        if need[a] > 0:
            need[a] -= 1
            out.append((s, o, a, k, e))
            continue
        cands = [i for i in range(4) if need[i] > 0]
        pick = None
        for t in cands:
            if not (DIGIT.search(o[a]) and DIGIT.search(o[t])):
                pick = t
                break
        if pick is None:
            pick = cands[0]
        need[pick] -= 1
        new = list(o)
        new[a], new[pick] = new[pick], new[a]
        out.append((s, new, pick, k, e))
    return out


CKS = scatter(CKS)
ZZ = scatter(ZZ)
print('常识答案分布：', dict(sorted(Counter(x[2] for x in CKS).items())))
print('政治答案分布：', dict(sorted(Counter(x[2] for x in ZZ).items())))


def render_item(idx, item):
    s, o, a, k, e = item
    lines = ['**%d.** %s' % (idx, s)]
    for j, opt in enumerate(o):
        lines.append('%s. %s' % (LET[j], opt))
    return '\n'.join(lines)


SECS1 = [
    ('一、时政与广东政策（1—10）', 0, 10),
    ('二、广东省情与粤港澳大湾区（11—30）', 10, 30),
    ('三、法律常识（31—50）', 30, 50),
    ('四、经济常识（51—60）', 50, 60),
    ('五、科技与生活（61—72）', 60, 72),
    ('六、人文历史（73—84）', 72, 84),
    ('七、地理国情（85—92）', 84, 92),
    ('八、公文与管理（93—100）', 92, 100),
]
SECS2 = [
    ('一、最新时政（101—110）', 0, 10),
    ('二、马克思主义基本原理（111—130）', 10, 30),
    ('三、毛泽东思想（131—140）', 30, 40),
    ('四、中国特色社会主义理论体系（141—150）', 40, 50),
    ('五、习近平新时代中国特色社会主义思想（151—185）', 50, 85),
    ('六、党史党建（186—200）', 85, 100),
]


def render():
    m = []
    m.append('# 广东省考每日刷题 · 第 011 期')
    m.append('')
    m.append('**日期**：2026-11-24　|　**科目**：常识判断 100 题 + 政治理论 100 题')
    m.append('**本期阶次**：二阶 · 反向辨析（不属于 / 错误的是 / 提法归属）')
    m.append('**时政板块**：主 C5（2026 年 8 月）｜副 C18（8 月·健康中国与防灾）')
    m.append('**建议用时**：常识 40 分钟（单题 25 秒）／政治理论 40 分钟（单题 25 秒）')
    m.append('**目标正确率**：常识 ≥ 70%，政治理论 ≥ 85%')
    m.append('')
    m.append('> 本期为二阶：时政 20 题以“下列表述错误的是”“不属于……的是”为主，考的是把讲义标注的常见错误项挑出来，不再只问时间地点。')
    m.append('> 主板块出 10 题（常识 5＋政治理论 5），副板块出 10 题（常识 5＋政治理论 5），20 题落在 20 个不同考点上，无重复。')
    m.append('> **板块说明**：主板块 C5 为 2026 年 8 月（江泽民同志诞辰 100 周年、吉隆泥石流、健康中国、防灾减灾、海油安澜号、C919、人形机器人运动会、地热、卫健公报、生态环境法典）。副板块 C18 为 8 月的文件与部署（生态保护“十五五”规划、全民医疗保障“十五五”规划、下沉市场意见、政绩观重要指示、防灾减灾、农业法）。C5 与 C18 同属 8 月，**同月不重出**：健康中国、防灾减灾等交叉主题只在 C5 或 C18 一侧出题，另一侧换事件；本轮 C5 取“健康中国＋灾害事件”，C18 取“防灾减灾文件精神＋政策文件”，两组的设问对象没有交集。')
    m.append('> **插期说明**：11-21（第 008 期）已于 11-19 生成，按“取编排表内第一个尚无文件的日期”顺延，本期对应 11-24 第 011 期。')
    m.append('> 广东侧重“大湾区与自贸区”，法律侧重行政复议法（另含《关于加强党建带团建工作的意见》《党政领导干部生态环境损害责任追究办法》两道新规），科技侧重能源与双碳，人文侧重岭南文化（含 6 道岭南），政治理论侧重习近平新时代中国特色社会主义思想·文化（151—168 集中 18 题）。')
    m.append('> 错题只记考点编号（如 C5-08、C18-03），二刷时回查《时政考点库.md》C5 段与《时政素材_2026.md》8 月段。')
    m.append('')
    m.append('---')
    m.append('')
    m.append('## 第一部分　常识判断（第 1—100 题）')
    m.append('')
    for title, a0, a1 in SECS1:
        m.append('### ' + title)
        m.append('')
        for i in range(a0, a1):
            m.append(render_item(i + 1, CKS[i]))
            m.append('')
    m.append('---')
    m.append('')
    m.append('## 第二部分　政治理论（第 101—200 题）')
    m.append('')
    for title, a0, a1 in SECS2:
        m.append('### ' + title)
        m.append('')
        for i in range(a0, a1):
            m.append(render_item(101 + i, ZZ[i]))
            m.append('')
    m.append('---')
    m.append('')
    m.append('## 第三部分　答案与解析')
    m.append('')
    for title, base, data in [('常识判断（1—50）', 1, CKS[:50]),
                              ('常识判断（51—100）', 51, CKS[50:]),
                              ('政治理论（101—150）', 101, ZZ[:50]),
                              ('政治理论（151—200）', 151, ZZ[50:])]:
        m.append('### ' + title)
        m.append('')
        for i, (s, o, a, k, e) in enumerate(data):
            m.append('**%d. %s**　考点：%s｜%s' % (base + i, LET[a], k, e))
        m.append('')
    m.append('---')
    m.append('')
    m.append('## 错题登记')
    m.append('')
    m.append('| 题号 | 考点编号 | 错因 | 复盘日期 |')
    m.append('|---|---|---|---|')
    for _ in range(6):
        m.append('|  |  |  |  |')
    m.append('')
    m.append('**今日统计**：常识正确 ___/100，政治理论正确 ___/100，用时 ___ 分钟。')
    m.append('')
    m.append('**二阶自查**：本期 20 道时政题全部为反向辨析。若“错误的是”能挑出来、正向还原却说不全，说明记的是印象不是条目，回看考点库对应编号再默一遍。')
    return '\n'.join(m) + '\n'


out = HERE / '2026-11-24_第011期_常识100+政治理论100.md'
out.write_text(render(), encoding='utf-8')
print('已写入', out.name, out.stat().st_size, '字节')

txt = out.read_text(encoding='utf-8')
qs = re.findall(r'^\*\*(\d+)\.\*\* ', txt, re.M)
ans = re.findall(r'^\*\*(\d+)\. ([ABCD])\*\*', txt, re.M)
print('题干数：', len(qs), '答案数：', len(ans))
assert len(qs) == 200 and len(ans) == 200
assert [int(x) for x in qs] == list(range(1, 201))
assert [int(x[0]) for x in ans] == list(range(1, 201))
print('校验通过')
