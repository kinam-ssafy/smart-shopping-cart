"""
ble_scanner.py - BLE 디바이스 스캐너

이 모듈은 주변의 BLE 디바이스를 스캔하여 
특정 서비스 UUID를 광고하는 ESP32 디바이스를 찾습니다.
"""

import asyncio
from bleak import BleakScanner


async def find_addr_by_service_uuid(service_uuid: str, timeout: float = 8.0):
    """
    서비스 UUID로 BLE 디바이스 주소 탐색
    
    주변의 BLE 디바이스를 스캔하여 지정된 service_uuid를 광고하는
    디바이스의 MAC 주소를 반환합니다.
    
    Args:
        service_uuid: 찾고자 하는 BLE 서비스 UUID
        timeout: 스캔 타임아웃 시간 (초), 기본값 8초
        
    Returns:
        str | None: 발견된 디바이스의 MAC 주소, 못 찾으면 None
    """
    
    # 현재 실행 중인 이벤트 루프 참조
    loop = asyncio.get_running_loop()
    
    # 디바이스 발견 시 시그널링할 이벤트
    found_event = asyncio.Event()
    
    # 발견된 디바이스 주소 저장 (딕셔너리로 래핑하여 클로저에서 수정 가능)
    found_addr = {"addr": None}
    
    # UUID 비교를 위해 소문자로 정규화
    target = service_uuid.lower()

    def cb(device, advertisement_data):
        """
        BLE 스캔 콜백 함수
        
        디바이스가 발견될 때마다 호출됩니다.
        광고 데이터에서 service_uuids를 확인하여 대상 디바이스인지 판별합니다.
        
        Args:
            device: 발견된 BLE 디바이스 객체
            advertisement_data: 디바이스의 광고 데이터
        """
        # 광고 데이터에서 서비스 UUID 목록 추출
        su = getattr(advertisement_data, "service_uuids", None) or []
        
        # 대상 UUID가 광고 목록에 있고, 아직 찾지 못한 상태인 경우
        if target in [u.lower() for u in su] and not found_event.is_set():
            found_addr["addr"] = device.address
            print(f"[FOUND] {device.address} ({getattr(device,'name',None)})")
            
            # 메인 루프에서 이벤트 설정 (스레드 안전)
            loop.call_soon_threadsafe(found_event.set)

    # BLE 스캐너 생성 및 시작
    scanner = BleakScanner(cb)
    await scanner.start()
    
    try:
        # 디바이스 발견 또는 타임아웃까지 대기
        await asyncio.wait_for(found_event.wait(), timeout)
    except asyncio.TimeoutError:
        # 타임아웃 시 None 반환
        return None
    finally:
        # 스캐너 정리 (성공/실패 모두)
        await scanner.stop()

    return found_addr["addr"]
