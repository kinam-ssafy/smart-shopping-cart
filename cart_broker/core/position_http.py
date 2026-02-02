# core/position_http.py
import asyncio
import aiohttp

async def poll_position_http(
    url: str,
    interval_sec: float,
    on_position: callable,
    timeout_sec: float = 0.5,
):
    """
    HTTP /api/position 을 주기적으로 GET해서 on_position(pos_dict) 호출
    """
    timeout = aiohttp.ClientTimeout(total=timeout_sec)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            try:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    pos = await resp.json()
                on_position(pos)
            except Exception as e:
                print("[POS] http fetch error:", e)

            await asyncio.sleep(interval_sec)


async def fetch_position_http(url: str, timeout_sec: float = 0.5) -> dict:
    """
    HTTP /api/position 을 1회 GET하여 position dict 반환
    """
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
