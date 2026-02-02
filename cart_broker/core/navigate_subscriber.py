"""
navigate_subscriber.py - navigate 토픽 구독 처리

MQTT로 들어오는 navigate payload를 파싱하고 검증합니다.
"""

import asyncio
import time
import json
from typing import Optional, Tuple

from core.navigate_http import send_navigate_http


def parse_navigate_payload(payload: str) -> Optional[Tuple[float, float]]:
    """
    navigate payload(JSON)에서 x,y를 파싱

    Args:
        payload: JSON 문자열 (예: {"x": 1.0, "y": 2.0})

    Returns:
        (x, y) 튜플 또는 None
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None

    x = data.get("x")
    y = data.get("y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None

    return float(x), float(y)


def make_navigate_handler(
    loop: asyncio.AbstractEventLoop,
    navigate_url: str,
    min_interval_sec: float,
):
    """
    MQTT on_message 콜백에서 사용할 핸들러 생성

    Returns:
        handler(topic, payload)
    """
    last_sent_at = 0.0

    def handler(topic: str, payload: str):
        parsed = parse_navigate_payload(payload)
        if not parsed:
            print(f"[MQTT SUB] invalid payload: {payload}")
            return

        x, y = parsed
        print(f"[MQTT SUB] {topic} -> x={x} y={y}")

        if not navigate_url:
            print("[MQTT SUB] navigate_url is empty; skip HTTP")
            return

        nonlocal last_sent_at
        now = time.monotonic()
        if now - last_sent_at < min_interval_sec:
            return
        last_sent_at = now

        fut = asyncio.run_coroutine_threadsafe(
            send_navigate_http(navigate_url, x, y, theta=0.0),
            loop,
        )

        def _done_cb(f):
            try:
                f.result()
                print("[NAV] http ok")
            except Exception as e:
                print("[NAV] http error:", e)

        fut.add_done_callback(_done_cb)

    return handler
