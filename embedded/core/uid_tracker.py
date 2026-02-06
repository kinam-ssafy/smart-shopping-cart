"""
uid_tracker.py - RFID UID 추적 모듈

이 모듈은 RFID 태그 UID의 활성 상태를 추적합니다.
TTL(Time-To-Live) 기반으로 일정 시간 동안 감지되지 않은 태그를 자동 만료 처리합니다.
"""

import time
from dataclasses import dataclass, field


def parse_msg(s: str):
    """
    ESP32에서 수신한 RFID 메시지 파싱
    
    메시지 형식: R{리더번호},{UID길이},{16진수UID}
    예시: R1,4,A1B2C3D4 → 리더 1번, 4바이트, UID A1:B2:C3:D4
    
    Args:
        s: ESP32에서 수신한 문자열 메시지
        
    Returns:
        tuple | None: (리더번호, UID길이, 포맷된UID) 또는 파싱 실패 시 None
    """
    try:
        # 쉼표로 분리
        parts = s.strip().split(",")
        
        # 형식 검증: 3개 파트, 첫 번째는 'R'로 시작
        if len(parts) != 3 or not parts[0].startswith("R"):
            return None
        
        # 리더 번호 추출 (R1 → 1)
        reader = int(parts[0][1:])
        
        # UID 길이 (바이트 단위)
        uid_len = int(parts[1])
        
        # 16진수 UID를 콜론으로 구분된 형식으로 변환
        # A1B2C3D4 → A1:B2:C3:D4
        hex_uid = parts[2].upper()
        uid = ":".join(hex_uid[i:i+2] for i in range(0, len(hex_uid), 2))
        
        return reader, uid_len, uid
    except:
        return None


@dataclass
class UIDInfo:
    """
    UID 정보 데이터클래스
    
    각 활성 UID에 대한 메타데이터를 저장합니다.
    
    Attributes:
        last_seen: 마지막으로 감지된 시간 (monotonic 타임스탬프)
        uid_len: UID의 바이트 길이
        readers: 이 UID를 감지한 리더 번호들의 집합
    """
    last_seen: float      # 마지막 감지 시간
    uid_len: int          # UID 길이 (바이트)
    readers: set[int] = field(default_factory=set)  # 감지한 리더 목록


class UIDTracker:
    """
    UID 활성 상태 추적기
    
    RFID 태그의 활성 상태를 TTL 기반으로 관리합니다.
    일정 시간 동안 감지되지 않은 태그는 자동으로 만료 처리됩니다.
    
    Attributes:
        ttl_sec: UID 만료 시간 (초)
        active: 현재 활성 상태인 UID 딕셔너리
    """
    
    def __init__(self, ttl_sec: float):
        """
        Args:
            ttl_sec: UID 만료 시간 (초) - 이 시간 동안 감지 안되면 삭제
        """
        self.ttl_sec = ttl_sec
        self.active: dict[str, UIDInfo] = {}  # UID → UIDInfo 매핑

    def format_active(self) -> str:
        """
        현재 활성 UID 목록을 문자열로 포맷
        
        Returns:
            str: "UID1, UID2, ..." 형식 또는 비어있으면 "∅"
        """
        return "∅" if not self.active else ", ".join(sorted(self.active.keys()))

    def touch(self, reader: int, uid_len: int, uid: str) -> bool:
        """
        UID 터치 (활성 상태 갱신)
        
        태그가 감지될 때마다 호출하여 마지막 감지 시간을 갱신합니다.
        새 UID인 경우 활성 목록에 추가합니다.
        
        Args:
            reader: 태그를 감지한 리더 번호
            uid_len: UID의 바이트 길이
            uid: 포맷된 UID 문자열 (예: A1:B2:C3:D4)
            
        Returns:
            bool: 새 UID가 추가되었으면 True, 기존 UID 갱신이면 False
        """
        now = time.monotonic()
        
        if uid not in self.active:
            # 새 UID 추가
            self.active[uid] = UIDInfo(
                last_seen=now, 
                uid_len=uid_len, 
                readers={reader}
            )
            return True
        
        # 기존 UID - 마지막 감지 시간 갱신 및 리더 추가
        info = self.active[uid]
        info.last_seen = now
        info.readers.add(reader)
        return False

    def expire(self) -> list[str]:
        """
        만료된 UID 제거
        
        TTL 시간이 지난 UID를 활성 목록에서 제거합니다.
        
        Returns:
            list[str]: 제거된 UID 목록
        """
        now = time.monotonic()
        removed = []
        
        # 딕셔너리 순회 중 삭제를 위해 list()로 복사
        for uid, info in list(self.active.items()):
            # TTL 초과 여부 확인
            if now - info.last_seen > self.ttl_sec:
                self.active.pop(uid, None)
                removed.append(uid)
        
        return removed
