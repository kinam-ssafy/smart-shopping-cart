import asyncio
from bleak import BleakScanner

async def find_addr_by_service_uuid(service_uuid: str, timeout: float = 8.0):
    loop = asyncio.get_running_loop()
    found_event = asyncio.Event()
    found_addr = {"addr": None}
    target = service_uuid.lower()

    def cb(device, advertisement_data):
        su = getattr(advertisement_data, "service_uuids", None) or []
        if target in [u.lower() for u in su] and not found_event.is_set():
            found_addr["addr"] = device.address
            print(f"[FOUND] {device.address} ({getattr(device,'name',None)})")
            loop.call_soon_threadsafe(found_event.set)

    scanner = BleakScanner(cb)
    await scanner.start()
    try:
        await asyncio.wait_for(found_event.wait(), timeout)
    except asyncio.TimeoutError:
        return None
    finally:
        await scanner.stop()

    return found_addr["addr"]
