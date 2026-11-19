# -*- coding: utf-8 -*-
"""一条命令把改动覆盖到所有平台。

现在这个项目有四个出口，改完必须全部一致，否则手机上打开会看到旧版：
    1. 省考平台.html      —— 本地双击用
    2. _site/index.html   —— WorkBuddy 主站（可登录云同步）
    3. docs/index.html    —— GitHub Pages 镜像
    4. 线上裸文件          —— 主站与 Pages 的实际内容

用法：
    python publish_all.py                 # 用默认提交信息
    python publish_all.py "改了某某"       # 自定义提交信息

做三件事：重建 → 提交并推 GitHub → 校验主站是否已同步。
主站部署走 WorkBuddy 的部署工具，脚本调不到，所以最后会明确告诉你还要不要发。
"""
import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = "https://wbapp-cmvrw789ihbe3hosa43jcr.app.workbuddy.host/?sharecode=XD7NFFZQ3Y"
PAGES = "https://huichengh.github.io/gd-gongkao-quiz/"


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=HERE, text=True, **kw)


def build() -> None:
    print("== 1/3 重建 ==")
    r = run([sys.executable, "build_platform.py"], capture_output=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        raise SystemExit("构建失败，先修这个再说。")


def consistency() -> dict[str, str]:
    """三个产物必须字节一致，不一致说明有一份没写成功。"""
    paths = {
        "本地": HERE / "省考平台.html",
        "主站包": HERE / "_site" / "index.html",
        "Pages": HERE / "docs" / "index.html",
    }
    out = {}
    for name, p in paths.items():
        if not p.exists():
            raise SystemExit(f"{name} 产物不存在：{p}")
        out[name] = md5(p.read_bytes())
    if len(set(out.values())) != 1:
        raise SystemExit(f"三份产物不一致，别推：{out}")
    print("   三份产物一致 md5=" + list(out.values())[0])
    return out


def commit_and_push(message: str) -> None:
    print("== 2/3 提交并推 GitHub ==")
    run(["git", "add", "-A"], check=True)
    st = run(["git", "status", "--porcelain"], capture_output=True).stdout.strip()
    force = "--force" in sys.argv
    if not st and not force:
        # 内容没变还推，只会在远端堆一堆空提交，没意义。
        print("   工作区无改动，跳过推送")
        return
    if st:
        run(["git", "-c", "user.name=huichengh",
             "-c", "user.email=huichengh@users.noreply.github.com",
             "commit", "-m", message], check=True)
        print("   已提交：" + message.splitlines()[0])
    r = run([sys.executable, "push_via_api.py"], capture_output=True)
    tail = [ln for ln in r.stdout.strip().splitlines() if ln.startswith(("commit", "url"))]
    print("   " + " | ".join(tail) if tail else r.stderr.strip()[:300])
    if r.returncode != 0:
        raise SystemExit("推送失败。")


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read()
    except Exception as e:
        print(f"   取不到 {url[:52]}…（{type(e).__name__}）")
        return None


def verify(local: dict[str, str]) -> None:
    print("== 3/3 校验线上 ==")
    want = local["本地"]

    page = fetch(PAGES)
    if page is not None:
        ok = md5(page) == want
        print(f"   GitHub Pages：{'已是最新' if ok else '还是旧版（Pages 有延迟，等 1-2 分钟再看）'}")

    main = fetch(PRIMARY)
    if main is None:
        print("   主站：取不到，需手动确认")
        return
    if md5(main) == want:
        print("   主站：已是最新")
    else:
        print("   主站：还是旧版 —— 需要用部署工具再发一次（directory 指到 _site）")


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "更新题库与功能"
    build()
    local = consistency()
    commit_and_push(message)
    verify(local)


if __name__ == "__main__":
    main()
