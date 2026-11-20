"""截图看版式：南网首页 / 背题 / 刷题 / 成绩，手机宽度 390。"""
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

EDGE = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
PORT = 9334
BASE = Path(__file__).parent
PAGE = (BASE / "省考平台.html").resolve().as_uri()
OUT = BASE / "_shots"
OUT.mkdir(exist_ok=True)

import websocket

proc = subprocess.Popen([
    EDGE, "--headless=new", "--disable-gpu", f"--remote-debugging-port={PORT}",
    "--user-data-dir=" + str(BASE / "_cdp_shot"), "--no-first-run",
    "--no-default-browser-check", "--window-size=390,1400", PAGE,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

ws_url = None
for _ in range(80):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=5) as r:
            for t in json.loads(r.read().decode()):
                if t.get("type") == "page" and "file://" in (t.get("url") or ""):
                    ws_url = t["webSocketDebuggerUrl"]
                    break
        if ws_url:
            break
    except Exception:
        pass
    time.sleep(0.3)

ws = websocket.create_connection(ws_url, timeout=25)
_id = [0]


def send(method, params=None, timeout=25):
    _id[0] += 1
    mid = _id[0]
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    t0 = time.time()
    while time.time() - t0 < timeout:
        raw = ws.recv()
        if not raw:
            continue
        o = json.loads(raw)
        if o.get("id") == mid:
            return o
    raise TimeoutError(method)


def ev(e):
    r = send("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": True, "userGesture": True})
    return r.get("result", {}).get("result", {}).get("value")


send("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})

for _ in range(80):
    if ev("typeof NANWANG!=='undefined' && NANWANG.length"):
        break
    time.sleep(0.2)


def shot(name):
    time.sleep(0.45)
    r = send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
    b64 = r["result"]["data"]
    (OUT / f"{name}.png").write_bytes(base64.b64decode(b64))
    print("shot", name)


ev("localStorage.clear(); location.reload()")
time.sleep(1.6)
ev("go('home')")
shot("01-home")
ev("go('nanwang')")
shot("02-nan-start")
ev("startStudy()")
shot("03-nan-study")
ev("(()=>{$('#nSstar').click();goStudy(1)})()")
shot("04-nan-study-fav")
ev("nView='run';startNanSet()")
shot("05-nan-run")
ev("(()=>{const q=nById(nset.ids[0]);chooseN('ABCD'[(q.ans+1)%4])})()")
shot("06-nan-run-answered")
ev("finishN()")
shot("07-nan-done")

ws.close()
proc.kill()
print("done ->", OUT)
