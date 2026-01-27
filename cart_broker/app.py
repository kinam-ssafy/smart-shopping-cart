"""
app.py - Cart Broker 메인 진입점

이 모듈은 스마트 쇼핑 카트 시스템의 브로커 애플리케이션입니다.
ESP32 BLE 디바이스로부터 RFID 태그 UID를 수신하여 MQTT 브로커로 전송합니다.

실행 흐름:
1. MQTT 브로커에 연결
2. BLE 스캔으로 ESP32 디바이스 탐색
3. ESP32와 BLE 연결 후 RFID 태그 UID 수신
4. UID 변경 시 MQTT로 발행
"""

import asyncio
from core.config import settings
from core.mqtt_client import mqtt_connect, publish_uid_list
from core.ble_scanner import find_addr_by_service_uuid
from core.uid_tracker import UIDTracker
from core.ble_session import run_ble_session


async def main():
    """
    메인 비동기 함수
    
    전체 애플리케이션의 실행 흐름을 관리합니다.
    MQTT 연결 → BLE 스캔 → BLE 세션 실행
    """
    
    # ========================================
    # 1단계: MQTT 브로커 연결
    # ========================================
    mqttc = mqtt_connect(
        settings.mqtt_host,
        settings.mqtt_port,
        settings.mqtt_id,
        settings.mqtt_pw,
    )
    print("[MQTT] connected")

    # ========================================
    # 2단계: ESP32 BLE 디바이스 탐색
    # ========================================
    # service_uuid를 기준으로 ESP32 디바이스를 스캔하여 MAC 주소 획득
    addr = await find_addr_by_service_uuid(settings.service_uuid)
    
    if not addr:
        # ESP32를 찾지 못한 경우 종료
        print("[ERR] ESP32 not found")
        mqttc.loop_stop()
        mqttc.disconnect()
        return

    # ========================================
    # 3단계: UID 추적기 초기화
    # ========================================
    # TTL(Time-To-Live) 기반으로 활성 UID를 추적
    # uid_ttl_sec 시간 동안 감지되지 않으면 자동 만료
    tracker = UIDTracker(ttl_sec=settings.uid_ttl_sec)

    def on_active_changed(active_uids: list[str]):
        """
        활성 UID 목록이 변경될 때 호출되는 콜백
        
        UID가 추가되거나 만료될 때마다 MQTT로 현재 UID 목록을 발행합니다.
        
        Args:
            active_uids: 현재 활성 상태인 UID 목록 (정렬됨)
        """
        publish_uid_list(mqttc, settings.mqtt_topic, active_uids)

    # ========================================
    # 4단계: BLE 세션 실행
    # ========================================
    try:
        await run_ble_session(
            addr=addr,                              # ESP32 MAC 주소
            char_uuid=settings.char_uuid,           # RFID 데이터 특성 UUID
            tracker=tracker,                        # UID 추적기
            on_active_changed=on_active_changed,    # 변경 콜백
            expiry_check_sec=settings.expiry_check_sec,  # 만료 체크 주기
        )
    finally:
        # 종료 시 MQTT 연결 정리
        mqttc.loop_stop()
        mqttc.disconnect()
        print("[INFO] Exit")


# 스크립트 직접 실행 시 메인 함수 호출
if __name__ == "__main__":
    asyncio.run(main())
