"""
mqtt_client.py - MQTT 클라이언트 모듈

이 모듈은 MQTT 브로커와의 연결 및 메시지 발행을 담당합니다.
활성 UID 목록이 변경될 때마다 MQTT 토픽으로 발행합니다.
"""

import json
from datetime import datetime
import paho.mqtt.client as mqtt


def now_str() -> str:
    """
    현재 시간을 문자열로 반환
    
    Returns:
        str: "YYYY-MM-DD HH:MM:SS" 형식의 현재 시간
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def mqtt_connect(host: str, port: int, user: str, pw: str):
    """
    MQTT 브로커에 연결
    
    인증 정보를 사용하여 MQTT 브로커에 연결하고,
    백그라운드 루프를 시작합니다.
    
    Args:
        host: MQTT 브로커 호스트 주소
        port: MQTT 브로커 포트 번호
        user: 인증 사용자명
        pw: 인증 비밀번호
        
    Returns:
        mqtt.Client: 연결된 MQTT 클라이언트 인스턴스
    """
    # MQTT 클라이언트 생성 (Callback API 버전 2 사용)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # 인증 정보 설정
    c.username_pw_set(user, pw)
    
    # 브로커에 연결 (keepalive: 60초)
    c.connect(host, port, 60)
    
    # 백그라운드 네트워크 루프 시작
    # 별도 스레드에서 메시지 송수신 처리
    c.loop_start()
    
    return c


def publish_uid_list(client, topic: str, active_uids: list[str]):
    """
    활성 UID 목록을 MQTT로 발행
    
    현재 활성 상태인 UID 목록을 JSON 형식으로 MQTT 토픽에 발행합니다.
    
    Args:
        client: MQTT 클라이언트 인스턴스
        topic: 발행할 MQTT 토픽 (예: cart/1)
        active_uids: 현재 활성 UID 목록
        
    발행 메시지 형식:
        {
            "uids": ["A1:B2:C3:D4", "E5:F6:G7:H8"],
            "time": "2026-01-27 16:30:00"
        }
    """
    # 페이로드 구성
    payload = {
        "uids": active_uids,  # 활성 UID 목록
        "time": now_str()     # 발행 시간
    }
    
    # JSON으로 직렬화하여 발행
    # qos=1: 최소 한 번 전송 보장
    # retain=True: 브로커가 마지막 메시지 유지 (새 구독자에게 즉시 전달)
    client.publish(
        topic, 
        json.dumps(payload, ensure_ascii=False), 
        qos=1, 
        retain=True
    )

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def publish_position(client, topic: str, pos: dict):
    """
    위치 정보를 MQTT로 발행

    Args:
        client: MQTT 클라이언트
        topic: 예: cart/1/position
        pos: HTTP에서 받아온 위치 JSON (x,y,theta,...)
    """
    payload = {
        "x": pos.get("x"),
        "y": pos.get("y"),
        "theta": pos.get("theta"),
        "theta_rad": pos.get("theta_rad"),
        "uncertainty": pos.get("uncertainty", {"x": 0.0, "y": 0.0}),
        "timestamp": pos.get("timestamp"),     # 서버/센서 타임
        "updated_at": pos.get("updated_at"),   # 서버가 찍은 ISO
        "time": now_str(),                     # 브로커 발행 시각(로컬)
    }

    client.publish(
        topic,
        json.dumps(payload, ensure_ascii=False),
        qos=1,
        retain=True,
    )


def subscribe_topic(client, topic: str, on_message, qos: int = 0):
    """
    MQTT 토픽을 구독하고 메시지 콜백을 등록

    Args:
        client: MQTT 클라이언트
        topic: 구독 토픽
        on_message: (topic, payload) 콜백
        qos: QoS 레벨
    """
    def _on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:
            payload = repr(msg.payload)
        on_message(msg.topic, payload)

    client.on_message = _on_message
    client.subscribe(topic, qos=qos)
