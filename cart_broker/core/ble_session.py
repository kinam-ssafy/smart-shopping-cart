# ble_session.py
import asyncio
from bleak import BleakClient
from uid_tracker import parse_msg, UIDTracker

async def run_ble_session(
    addr: str,
    char_uuid: str,
    tracker: UIDTracker,
    on_active_changed, # callable(active_uids: list[str]) -> None
    expiry_check_sec: float,
):
    stop_evt = asyncio.Event()

    def on_notify(_, data: bytearray):
        s = data.decode(errors="ignore")
        parsed = parse_msg(s)
        if not parsed:
            return
        reader, uid_len, uid = parsed
        is_new = tracker.touch(reader, uid_len, uid)
        if is_new:
            print(f"[ADD] {uid} | active={tracker.format_active()}")
            on_active_changed(sorted(tracker.active.keys()))

    async def expiry_worker():
        while not stop_evt.is_set():
            removed = tracker.expire()
            if removed:
                for uid in removed:
                    print(f"[DEL] {uid} | active={tracker.format_active()}")
                on_active_changed(sorted(tracker.active.keys()))
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=expiry_check_sec)
            except asyncio.TimeoutError:
                pass

    print("[INFO] Connecting BLE", addr)

    async with BleakClient(addr) as client:
        expiry_task = None
        try:
            print("[INFO] Connected:", client.is_connected)
            await client.start_notify(char_uuid, on_notify)
            expiry_task = asyncio.create_task(expiry_worker())
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Ctrl+C")
        finally:
            stop_evt.set()
            if expiry_task:
                try:
                    await expiry_task
                except:
                    pass
            try:
                await client.stop_notify(char_uuid)
            except:
                pass
            try:
                if client.is_connected:
                    await client.disconnect()
            except:
                pass
