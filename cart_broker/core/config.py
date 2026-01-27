"""
config.py - 애플리케이션 설정 관리

이 모듈은 Cart Broker의 모든 설정값을 중앙에서 관리합니다.
환경변수(.env)와 하드코딩된 상수를 Settings 데이터클래스로 통합합니다.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv("../.env")


@dataclass(frozen=True)
class Settings:
    """
    애플리케이션 설정 데이터클래스
    
    frozen=True로 설정하여 불변(immutable) 객체로 생성됩니다.
    런타임 중 설정값 변경을 방지합니다.
    
    Attributes:
        service_uuid: ESP32 BLE 서비스 UUID (디바이스 식별용)
        char_uuid: RFID 데이터 수신 특성(Characteristic) UUID
        uid_ttl_sec: UID 만료 시간 (초) - 이 시간 동안 감지 안되면 삭제
        expiry_check_sec: 만료 체크 주기 (초)
        mqtt_host: MQTT 브로커 호스트 주소
        mqtt_port: MQTT 브로커 포트 번호
        mqtt_topic: MQTT 발행 토픽 (예: cart/1)
        mqtt_id: MQTT 인증 사용자명
        mqtt_pw: MQTT 인증 비밀번호
    """
    
    # ========================================
    # BLE 설정 (ESP32 디바이스 연결용)
    # ========================================
    # ESP32에서 광고(Advertise)하는 서비스 UUID
    # 이 UUID로 BLE 스캔 시 ESP32를 식별합니다
    service_uuid: str = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a01"
    
    # RFID 태그 데이터를 수신하는 특성(Characteristic) UUID
    # 이 특성에서 Notify를 구독하여 태그 데이터를 받습니다
    char_uuid: str = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a02"

    # ========================================
    # UID 추적 설정
    # ========================================
    # UID 만료 시간 (Time-To-Live)
    # 이 시간 동안 태그가 감지되지 않으면 활성 목록에서 제거됩니다
    uid_ttl_sec: float = 5.0
    
    # 만료된 UID를 체크하는 주기
    # 짧을수록 반응이 빠르지만 CPU 사용량이 증가합니다
    expiry_check_sec: float = 0.5

    # ========================================
    # MQTT 설정 (환경변수에서 로드)
    # ========================================
    # MQTT 브로커 호스트 주소 (IP 또는 도메인)
    mqtt_host: str = os.getenv("MQTT_HOST", "")
    
    # MQTT 브로커 포트 (기본: 1883, TLS: 8883)
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    
    # MQTT 발행 토픽 (예: cart/1, cart/2 등 카트별로 구분)
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "")
    
    # MQTT 인증 정보
    mqtt_id: str = os.getenv("MQTT_ID", "")
    mqtt_pw: str = os.getenv("MQTT_PW", "")


# 전역 설정 인스턴스
# 다른 모듈에서 from core.config import settings로 사용
settings = Settings()
