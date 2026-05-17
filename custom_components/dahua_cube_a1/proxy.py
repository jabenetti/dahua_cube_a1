"""Aiohttp-based CGI proxy that mimics Dahua eventManager.cgi with Digest auth."""

import hashlib
import re
import time
import asyncio
from aiohttp import web
from aiohttp.web import StreamResponse
from queue import Queue

cameras = []


def _parse_digest_auth(header: str, username: str, password: str) -> bool:
    if not header or not header.startswith("Digest "):
        return False
    digest_re = re.compile(r'(\w+)=(?:"([^"]+)"|([^\s,]+))')
    parts = {m.group(1): m.group(2) or m.group(3) for m in digest_re.finditer(header[7:])}
    if parts.get("username") != username:
        return False
    realm = parts.get("realm", "Dahua")
    nonce = parts.get("nonce", "")
    nc = parts.get("nc", "00000001")
    cnonce = parts.get("cnonce", "")
    qop = parts.get("qop", "auth")
    uri = parts.get("uri", "")
    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"GET:{uri}".encode()).hexdigest()
    response_calc = hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()).hexdigest()
    return response_calc == parts.get("response", "")


async def event_manager(request: web.Request):
    auth_header = request.headers.get("Authorization", "")
    username = request.app["proxy_username"]
    password = request.app["proxy_password"]

    if not _parse_digest_auth(auth_header, username, password):
        nonce = str(int(time.time()))
        return web.Response(
            text="Unauthorized",
            status=401,
            headers={"WWW-Authenticate": f'Digest realm="Dahua", nonce="{nonce}", qop="auth", algorithm=MD5'}
        )

    action = request.query.get("action")
    if action != "attach":
        return web.Response(text="Only attach action supported", status=400)

    response = StreamResponse(
        status=200,
        headers={
            "Content-Type": "multipart/x-mixed-replace; boundary=myboundary",
            "Cache-Control": "no-cache",
        },
    )
    await response.prepare(request)

    try:
        while True:
            if time.time() % 5 < 0.1:
                await response.write(
                    b"--myboundary\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nHeartbeat\r\n\r\n"
                )
                await response.drain()

            for cam in cameras:
                if not cam.event_queue.empty():
                    event = cam.event_queue.get_nowait()
                    data_str = (
                        f'Code={event["code"]};action={event["action"]};index={event["index"]};'
                        f'data={{{event["data"]}}}\r\n'
                    )
                    data = data_str.encode()
                    header = (
                        f"--myboundary\r\nContent-Type: text/plain\r\nContent-Length: {len(data)}\r\n\r\n"
                    ).encode()
                    await response.write(header + data + b"\r\n")
                    await response.drain()

            await asyncio.sleep(0.1)
    except Exception:
        pass  # silent fail - keep server alive
    finally:
        await response.write_eof()
    return response


def start_proxy(port: int, username: str, password: str, cameras_list):
    global cameras
    cameras = cameras_list

    app = web.Application()
    app["proxy_username"] = username
    app["proxy_password"] = password
    app.router.add_get("/cgi-bin/eventManager.cgi", event_manager)

    runner = web.AppRunner(app)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_server():
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        await asyncio.Event().wait()

    task = asyncio.create_task(run_server())
    return runner, task