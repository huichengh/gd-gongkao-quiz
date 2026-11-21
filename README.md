# 广东省考刷题平台

一个单文件网页，装着自己的题库。打开就能刷，不用装东西。

- 主站（可登录云端同步）：https://wbapp-cmvrw789ihbe3hosa43jcr.app.workbuddy.host/?sharecode=XD7NFFZQ3Y
- 镜像（GitHub Pages，随手打开，不连云端）：https://huichengh.github.io/gd-gongkao-quiz/

## 里面有什么

| 模块 | 内容 | 交互 |
| --- | --- | --- |
| 每日刷题 | 11 期 × 200 题（100 常识判断 + 100 政治理论），按日期切换 | 点选项即时判对错、给解析、可星标 |
| 成语记忆 | 848 条成语，逐条给释义与用法 | 遮盖自测、收藏 |
| 知识点 | 82 张卡片，9 个分类（规划蓝图／习思想／战略布局／党建党规／马原／毛中特／时政数字／2026 会议／广东省情） | 卡片与全览两种视图、搜索、遮盖回忆 |
| 数量关系 | 86 道（工程问题 46 + 集合容斥 40），分数精确计算 | 按题型筛选、一组 10 题、计时、交卷、错题回看 |
| 言语理解 | 60 道（选词填空 23 + 片段阅读 21 + 语句表达 16） | 按题型筛选、一组 10 题、计时、交卷、错题回看 |
| 南方电网 | 2552 道，9 类（计算机 763／经济学 524／岗位模拟卷 292／常识判断 290／法律 279／管理学 259／马原 61／公文 57／企业文化 27） | 背题模式（题干＋解析直接看）、随机刷题一组 10 题、只看收藏、按科目筛选 |

刷题进度和收藏默认存在浏览器本地。登录后同步到云端，手机和电脑共用一份。

## 本地跑

```bash
python server.py           # 起服务，127.0.0.1:8760
浏览器打开 http://127.0.0.1:8760/
```

`server.py` 用 `ThreadingHTTPServer` 存进度到 `_data/*.json`（tmp + fsync + os.replace，留 60 份备份）。这是本机存储，不连云。

## 改完发布（一条命令覆盖全部）

```bash
python publish_all.py "这次改了什么"
```

它会：重建 → 校验三份产物字节一致 → 提交并推 GitHub → 抓主站和 Pages 的线上文件比 md5，告诉你哪一处还是旧版。

主站部署走 WorkBuddy 的部署工具，脚本调不到；若脚本提示「主站还是旧版」，用部署工具再发一次（`directory` 指到 `_site`）。

只重建不发布可以单独跑：

```bash
python build_platform.py
```

产出三份，内容必须完全一致：

- `省考平台.html` —— 本地直接双击可开
- `_site/index.html` —— WorkBuddy 主站（可登录云同步）
- `docs/index.html` —— GitHub Pages 镜像（Pages 只认根目录或 `/docs`）

页面是把题库 JSON 注入模板占位符生成的：`__QUIZ__` / `__VOCAB__` / `__KNOW__` / `__MATH__` / `__YANYU__` / `__NANWANG__` / `__CLOUD__` / `__CLOUD_SDK__`。云 SDK 内联进 HTML，不走 CDN（国内访问 jsdelivr 会失败）。

## 各脚本

| 文件 | 作用 |
| --- | --- |
| `build_platform.py` | 主构建，把题库合成单文件页面 |
| `build_quiz.py` | 解析 Markdown 题库（`**1.**` 题干 / `A.` 选项 / `**1. B**　考点：…｜解析`） |
| `build_vocab.py`、`extract_vocab.py` | 成语提取与清洗 |
| `gen_math.py`、`gen_rcc.py` | 生成数量关系题（工程问题 / 集合容斥），答案用 `Fraction` 重算并断言 |
| `gen_yanyu.py` | 生成言语理解题，打散答案时同步校正解析里的选项指向 |
| `gen_nanwang.py` | 从 `C:/Users/84307/Desktop/南网中公` 的 PDF 提取南方电网题（锚点法切题 + 题号序列 LCS 对齐答案） |
| `gen_009.py` | 第 009 期（APEC 专题）的生成脚本，沿用可直接改期号 |
| `gen_know_meetings.py` | 往 `知识点.json` 插入「2026 会议」分类（全国与广东各场会议的时间、议程、成果） |
| `rebalance.py` | 打散答案分布，让 A/B/C/D 不至于一边倒 |
| `fix_headings.py` | 修复讲义自带编号被误当成新题目的问题 |
| `publish_all.py` | 一键：重建 + 校验一致性 + 推 GitHub + 核对线上 |
| `push_via_api.py` | 走 Git Data API 推 GitHub（本机 git push 不通） |
| `server.py` | 本地服务 |
| `cloud_config.json` | 云服务的 endpoint 与 publishable key |

## 数据

- 每期题库：`2026-MM-DD_第NNN期_常识100+政治理论100.md`（HTML 是同期单页版）
- `知识点.json`（82 张卡）、`数量关系.json`（86 题）、`言语理解.json`（60 题）、`南网.json`（2552 题）、`_vocab/items.json`（848 条成语，由 `extract_vocab.py` 从 PDF 提取后 `build_vocab.py` 清洗）
- `时政素材_2026.md`、`时政考点库.md` —— 出题取材的时政材料

`_src/`、`_src2/` 是时政讲义的拆分文本，属于付费材料，没有入库。

## 说明

题目为自行编写，取材于公开时政新闻与考试大纲；不含任何培训机构的讲义原文或原题。时政、法条、招考政策会变，具体以官方最新公告为准。

**例外是「南方电网」模块**：那 2552 道是从本机 `C:/Users/84307/Desktop/南网中公` 的教材 PDF 里提取的，属于培训机构的资料，只作个人备考自用。代码里做了硬隔离——`南网.json` 单独一个文件、题目 id 统一 `n` 前缀、`load_nanwang()` 只喂给南网视图，不进每日刷题/成语/知识点/数量关系/言语理解任何一个模块，云端字段也是独立的 `nstat`/`nfavs`。

云同步依赖一张 `study_state` 表（行级安全，每人只能读写自己那一行），首次登录时把本机记录作为初始数据上传，之后按 `updatedAt` 取较新的一份。

## 怎么更新这个仓库

改完 `python build_platform.py`，再：

```bash
git add -A && git commit -m "说明"
python push_via_api.py
```

不走 `git push` 是有原因的：这台机器只有 `api.github.com` 通，`github.com:443` 的 CONNECT 隧道会被代理拒掉（502），git 协议传不上去。`push_via_api.py` 改用 Git Data API（blobs → tree → commit → ref），效果一样。

