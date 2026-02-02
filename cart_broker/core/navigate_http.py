"""
navigate_http.py - navigate 명령 HTTP 전송
"""

import aiohttp


async def send_navigate_http(
    url: str,
    x: float,
    y: float,
    theta: float | None = None,
    timeout_sec: float = 0.5,
):
    """
    navigate 좌표를 HTTP로 전송

    Args:
        url: POST 대상 URL
        x: 목표 x 좌표
        y: 목표 y 좌표
        theta: 목표 theta (없으면 전송 생략)
        timeout_sec: 요청 타임아웃
    """
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    payload = {"x": x, "y": y}
    if theta is not None:
        payload["theta"] = theta
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            if resp.status >= 400:
                try:
                    body = await resp.text()
                except Exception:
                    body = ""
                raise RuntimeError(f"HTTP {resp.status} {body}")
