#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广东省考刷题 · 本地进度服务器

- 静态托管本目录（刷题页 + 各期单页）
- GET  /api/progress  读取进度快照
- POST /api/progress  写入进度快照（整体替换，按 updatedAt 判新旧）
- GET  /api/health    健康检查

进度落盘在 _data/progress.json，每次写入另存一份历史副本到 _data/backup/（保留最近 60 份）。
只监听 127.0.0.1，不对外网开放。
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# pythonw.exe 下 sys.stdout / sys.stderr 是 None，print 会抛异常导致进程秒退
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

HERE = Path(__file__).resolve().parent
DATA = HERE / "_data"
BACKUP = DATA / "backup"
SNAP = DATA / "progress.json"
PORT = int(os.environ.get("QUIZ_PORT", "8760"))
KEEP_BACKUPS = 60

# 允许的命名空间：/api/<名字> → _data/<名字>.json
SPACES = {
    "progress": DATA / "progress.json",
    "vocab": DATA / "vocab.json",
    "know": DATA / "know.json",
    "math": DATA / "math.json",
}

_lock = threading.Lock()

EMPTY = {"answers": {}, "favs": {}, "updatedAt": 0}


def ensure_dirs() -> None:
    DATA.mkdir(exist_ok=True)
    BACKUP.mkdir(exist_ok=True)


def read_snapshot(path: Path | None = None) -> dict:
    path = path or SNAP
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return dict(EMPTY)
        obj.setdefault("answers", {})
        obj.setdefault("favs", {})
        obj.setdefault("updatedAt", 0)
        return obj
    except FileNotFoundError:
        return dict(EMPTY)
    except Exception:
        # 文件损坏：留档后重建，不阻塞使用
        try:
            if path.exists():
                shutil.copy2(path, BACKUP / ("broken-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"))
        except Exception:
            pass
        return dict(EMPTY)


def write_snapshot(obj: dict, path: Path | None = None) -> None:
    path = path or SNAP
    ensure_dirs()
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = path.stem
    try:
        shutil.copy2(path, BACKUP / f"{prefix}-{stamp}.json")
        olds = sorted(BACKUP.glob(f"{prefix}-*.json"))
        for p in olds[:-KEEP_BACKUPS]:
            p.unlink(missing_ok=True)
    except Exception:
        pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    # 安静一点，只打需要的
    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stdout.write("%s  %s\n" % (time.strftime("%H:%M:%S"), fmt % args))
            sys.stdout.flush()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        if urlparse(self.path).path.startswith("/api/"):
            self.send_response(204)
            self._cors()
            self.end_headers()
        else:
            self.send_error(404)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            snap = read_snapshot()
            voc = read_snapshot(SPACES["vocab"])
            kno = read_snapshot(SPACES["know"])
            mth = read_snapshot(SPACES["math"])
            return self._json(200, {
                "ok": True,
                "answers": len(snap.get("answers", {})),
                "favs": len(snap.get("favs", {})),
                "updatedAt": snap.get("updatedAt", 0),
                "vocabFavs": len(voc.get("favs", {})),
                "knowFavs": len(kno.get("favs", {})),
                "mathDone": len(mth.get("answers", {})),
                "mathFavs": len(mth.get("favs", {})),
            })
        name = path[len("/api/"):] if path.startswith("/api/") else ""
        if name in SPACES:
            return self._json(200, read_snapshot(SPACES[name]))
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        name = path[len("/api/"):] if path.startswith("/api/") else ""
        if name not in SPACES:
            return self.send_error(404)
        store = SPACES[name]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > 8 * 1024 * 1024:
            return self._json(400, {"ok": False, "error": "bad length"})
        raw = self.rfile.read(n)
        try:
            incoming = json.loads(raw.decode("utf-8"))
            if not isinstance(incoming, dict):
                raise ValueError
        except Exception:
            return self._json(400, {"ok": False, "error": "bad json"})

        ans = incoming.get("answers") or {}
        fav = incoming.get("favs") or {}
        if not isinstance(ans, dict) or not isinstance(fav, dict):
            return self._json(400, {"ok": False, "error": "bad shape"})

        with _lock:
            stored = read_snapshot(store)
            ts_new = int(incoming.get("updatedAt") or 0)
            ts_old = int(stored.get("updatedAt") or 0)
            if ts_new < ts_old:
                # 服务器上的更新，让客户端改用服务器的
                return self._json(200, dict(stored, ok=False, stale=True))
            snap = {"answers": ans, "favs": fav, "updatedAt": ts_new}
            write_snapshot(snap, store)
        return self._json(200, {"ok": True, "updatedAt": ts_new,
                                "answers": len(ans), "favs": len(fav)})

    def end_headers(self):
        # 页面不缓存，改完刷新就是新的
        if self.path.endswith(".html") or "/api/" in self.path:
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def main():
    ensure_dirs()
    snap = read_snapshot()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("=" * 58)
    print("  广东省考刷题 · 本地服务器已启动")
    print(f"  打开： http://127.0.0.1:{PORT}/  （省考平台首页）")
    print(f"  数据： {SNAP}")
    print(f"  当前已存：作答 {len(snap.get('answers', {}))} 题 / 收藏 {len(snap.get('favs', {}))} 条")
    print("  关闭窗口即停止服务（进度已落盘，不会丢）")
    print("=" * 58)
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
