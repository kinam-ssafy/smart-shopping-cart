"""
ble_session.py - BLE 연결 세션 관리

이 모듈은 ESP32 BLE 디바이스와의 연결을 관리하고,
RFID 태그 데이터를 수신하여 UID 추적기에 전달합니다.
"""

import asyncio
from bleak import BleakClient
from .uid_tracker import parse_msg, UIDTracker


async def run_ble_session(
    addr: str,
    char_uuid: str,
    tracker: UIDTracker,
    on_active_changed,  # callable(active_uids: list[str]) -> None
    expiry_check_sec: float,
):
    """
    BLE 세션 실행
    
    ESP32에 BLE로 연결하고, RFID 태그 데이터를 지속적으로 수신합니다.
    새 태그 감지 또는 태그 만료 시 콜백을 호출합니다.
    
    Args:
        addr: ESP32 BLE MAC 주소
        char_uuid: RFID 데이터 특성 UUID
        tracker: UID 추적기 인스턴스
        on_active_changed: 활성 UID 목록 변경 시 호출될 콜백 함수
        expiry_check_sec: 만료 체크 주기 (초)
    """
    
    # 세션 종료 시그널 이벤트
    stop_evt = asyncio.Event()

    def on_notify(_, data: bytearray):
        """
        BLE Notify 수신 콜백
        
        ESP32에서 RFID 태그 데이터가 전송될 때마다 호출됩니다.
        데이터를 파싱하여 UID 추적기에 등록합니다.
        
        Args:
            _: 특성 핸들 (사용하지 않음)
            data: 수신된 바이너리 데이터
        """
        # 바이너리 데이터를 문자열로 디코딩
        s = data.decode(errors="ignore")
        
        # 메시지 파싱 (R{리더},{길이},{UID} 형식)
        parsed = parse_msg(s)
        if not parsed:
            return
            
        reader, uid_len, uid = parsed
        
        # UID 추적기에 터치 (새 UID면 True 반환)
        is_new = tracker.touch(reader, uid_len, uid)
        
        if is_new:
            # 새 태그 감지 시 로그 출력 및 콜백 호출
            print(f"[ADD] {uid} | active={tracker.format_active()}")
            on_active_changed(sorted(tracker.active.keys()))

    async def expiry_worker():
        """
        UID 만료 처리 워커
        
        주기적으로 만료된 UID를 체크하고 제거합니다.
        TTL 시간 동안 감지되지 않은 태그는 활성 목록에서 삭제됩니다.
        """
        while not stop_evt.is_set():
            # 만료된 UID 확인 및 제거
            removed = tracker.expire()
            
            if removed:
                # 만료된 태그가 있으면 로그 출력 및 콜백 호출
                for uid in removed:
                    print(f"[DEL] {uid} | active={tracker.format_active()}")
                on_active_changed(sorted(tracker.active.keys()))
            
            try:
                # 다음 체크까지 대기 (또는 종료 시그널 수신)
                await asyncio.wait_for(stop_evt.wait(), timeout=expiry_check_sec)
            except asyncio.TimeoutError:
                # 타임아웃은 정상 동작, 루프 계속
                pass

    print("[INFO] Connecting BLE", addr)

    # ========================================
    # BLE 클라이언트 연결 및 세션 유지
    # ========================================
    async with BleakClient(addr) as client:
        expiry_task = None
        
        try:
            print("[INFO] Connected:", client.is_connected)
            
            # RFID 데이터 특성에서 Notify 구독 시작
            await client.start_notify(char_uuid, on_notify)
            
            # 만료 체크 백그라운드 태스크 시작
            expiry_task = asyncio.create_task(expiry_worker())
            
            # 연결 유지 (무한 루프)
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            # Ctrl+C로 종료
            print("\n[INFO] Ctrl+C")
            
        finally:
            # ========================================
            # 정리 작업 (세션 종료 시)
            # ========================================
            
            # 종료 시그널 설정
            stop_evt.set()
            
            # 만료 워커 태스크 종료 대기
            if expiry_task:
                try:
                    await expiry_task
                except:
                    pass
            
            # Notify 구독 해제
            try:
                await client.stop_notify(char_uuid)
            except:
                pass
            
            # BLE 연결 해제
            try:
                if client.is_connected:
                    await client.disconnect()
            except:
                pass
