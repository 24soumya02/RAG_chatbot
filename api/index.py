import asyncio
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

ROOT = Path(__file__).resolve().parent.parent
PORT = 8500
BASE = f"http://127.0.0.1:{PORT}"
START_TIMEOUT = 120

app = FastAPI()

_proc: subprocess.Popen | None = None
_ready = False


def _ensure_server() -> None:
    global _proc, _ready
    if _ready and _proc is not None and _proc.poll() is None:
        return

    python_path = os.environ.get("PYTHONPATH")
    extra = os.pathsep.join(sys.path)
    env = {
        **os.environ,
        "PYTHONPATH": f"{python_path}{os.pathsep}{extra}" if python_path else extra,
        "STREAMLIT_SERVER_PORT": str(PORT),
        "STREAMLIT_SERVER_HEADLESS": "true",
    }
    _proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
            "--server.address=127.0.0.1",
            f"--server.port={PORT}",
            "--server.headless=true",
            "--server.enableXsrfProtection=false",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.monotonic() + START_TIMEOUT
    while time.monotonic() < deadline:
        if _proc.poll() is not None:
            _ready = False
            out, err = _proc.communicate()
            raise RuntimeError(
                "Streamlit process exited unexpectedly.\n"
                f"STDOUT:\n{out}\nSTDERR:\n{err}"
            )
        try:
            with urllib.request.urlopen(f"{BASE}/_stcore/health", timeout=1) as resp:
                if resp.status == 200:
                    _ready = True
                    return
        except Exception:
            time.sleep(0.5)

    _ready = False
    raise RuntimeError("Timed out waiting for Streamlit to start")


async def _ensure_ready() -> None:
    await asyncio.to_thread(_ensure_server)


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def proxy(path: str, request: Request):
    await _ensure_ready()
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "connection", "upgrade")
    }
    async with httpx.AsyncClient(timeout=300) as client:
        upstream = await client.request(
            request.method,
            f"{BASE}/{path}",
            params=request.query_params,
            headers=headers,
            content=await request.body(),
        )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={
            k: v
            for k, v in upstream.headers.items()
            if k.lower()
            not in (
                "connection",
                "keep-alive",
                "transfer-encoding",
                "upgrade",
                "content-length",
                "content-encoding",
            )
        },
    )


@app.websocket("/{path:path}")
async def ws_proxy(websocket: WebSocket, path: str):
    import websockets

    await _ensure_ready()
    params = urlencode(dict(websocket.query_params))
    suffix = f"?{params}" if params else ""
    ws_url = f"ws://127.0.0.1:{PORT}/{path}{suffix}"

    async def browser_to_upstream():
        while True:
            data = await websocket.receive()
            if data["type"] == "websocket.receive_text":
                await upstream.send(data["text"])
            elif data["type"] == "websocket.receive_bytes":
                await upstream.send(data["bytes"])

    async def upstream_to_browser():
        while True:
            data = await upstream.recv()
            if isinstance(data, str):
                await websocket.send_text(data)
            else:
                await websocket.send_bytes(data)

    try:
        async with websockets.connect(ws_url, subprotocols=["streamlit"]) as upstream:
            await websocket.accept(subprotocol="streamlit")
            await asyncio.gather(browser_to_upstream(), upstream_to_browser())
    except (WebSocketDisconnect, websockets.ConnectionClosed, OSError):
        pass