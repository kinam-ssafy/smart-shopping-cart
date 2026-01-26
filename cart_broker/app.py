# app.py
import asyncio
from config import settings
from mqtt_client import mqtt_connect, publish_uid_list
from ble_scanner import find_addr_by_service_uuid
from uid_tracker import UIDTracker
from ble_session import run_ble_session

async def main():
    mqttc = mqtt_connect(
        settings.mqtt_host,
        settings.mqtt_port,
        settings.mqtt_id,
        settings.mqtt_pw,
    )
    print("[MQTT] connected")

    addr = await find_addr_by_service_uuid(settings.service_uuid)
    if not addr:
        print("[ERR] ESP32 not found")
        mqttc.loop_stop()
        mqttc.disconnect()
        return

    tracker = UIDTracker(ttl_sec=settings.uid_ttl_sec)

    def on_active_changed(active_uids: list[str]):
        publish_uid_list(mqttc, settings.mqtt_topic, active_uids)

    try:
        await run_ble_session(
            addr=addr,
            char_uuid=settings.char_uuid,
            tracker=tracker,
            on_active_changed=on_active_changed,
            expiry_check_sec=settings.expiry_check_sec,
        )
    finally:
        mqttc.loop_stop()
        mqttc.disconnect()
        print("[INFO] Exit")

if __name__ == "__main__":
    asyncio.run(main())
