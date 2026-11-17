"""通过 GitHub REST API 推送提交（本机只放行了 api.github.com，git 协议连不通）。

空仓库先 PUT 一次 README 建出 main 分支，再用 Git Data API 提交整棵树：
blobs → tree → commit → 更新 refs/heads/main。
用法：python push_via_api.py
"""
import base64
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

REPO = "huichengh/gd-gongkao-quiz"
API = "https://api.github.com"
HERE = Path(__file__).resolve().parent

MESSAGE = None  # 由本地最后一次 commit 提供


def commit_message() -> str:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%B"], cwd=HERE, capture_output=True, text=True, check=True
    )
    return out.stdout.strip() or "update"


def token() -> str:
    out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


TOKEN = token()


def call(method: str, path: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        raise SystemExit(f"{method} {path} -> {e.code}: {body}")


def head_sha() -> str | None:
    try:
        return call("GET", f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]
    except SystemExit:
        return None


def bootstrap() -> str:
    """空仓库不能建 blob，先塞一个 README 把 main 生出来。"""
    readme = (HERE / "README.md").read_bytes()
    out = call("PUT", f"/repos/{REPO}/contents/README.md", {
        "message": "init",
        "content": base64.b64encode(readme).decode(),
    })
    return out["commit"]["sha"]


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=HERE, capture_output=True, check=True
    ).stdout
    return [HERE / n for n in out.decode("utf-8").split("\0") if n]


def main() -> None:
    parent = head_sha() or bootstrap()
    print("parent", parent)
    message = commit_message()

    files = tracked_files()
    tree = []
    for i, f in enumerate(files, 1):
        rel = f.relative_to(HERE).as_posix()
        blob = call("POST", f"/repos/{REPO}/git/blobs", {
            "content": base64.b64encode(f.read_bytes()).decode(),
            "encoding": "base64",
        })
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"[{i}/{len(files)}] {rel}  {f.stat().st_size} B")

    root = call("POST", f"/repos/{REPO}/git/trees", {"tree": tree})
    commit = call("POST", f"/repos/{REPO}/git/commits", {
        "message": message, "tree": root["sha"], "parents": [parent],
    })
    call("PATCH", f"/repos/{REPO}/git/refs/heads/main", {"sha": commit["sha"], "force": True})
    print("commit", commit["sha"])
    print("url", commit["html_url"])


if __name__ == "__main__":
    main()
