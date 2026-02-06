# 🛒 Cart Broker

**스마트 쇼핑 카트 RFID 태그 감지 브로커**

ESP32 BLE 디바이스로부터 RFID/NFC 태그 UID를 수신하여 MQTT 브로커로 중계하는 Python 애플리케이션입니다.

---

## 📋 목차

- [아키텍처](#아키텍처)
- [요구사항](#요구사항)
- [설치 및 실행](#설치-및-실행)
- [환경변수 설정](#환경변수-설정)
- [프로젝트 구조](#프로젝트-구조)
- [동작 원리](#동작-원리)
- [메시지 형식](#메시지-형식)

---

## 🏗️ 아키텍처

```
┌─────────────┐    BLE     ┌──────────────┐    MQTT     ┌───────────────┐
│   ESP32     │ ────────▶  │ cart_broker  │ ──────────▶ │  MQTT Broker  │
│ (RFID 리더) │  Notify    │  (Python)    │   Publish   │               │
└─────────────┘            └──────────────┘             └───────────────┘
                                                              │
                                                              ▼
                                                        Backend Server
                                                        (SSE로 프론트 전달)
```

---

## 📦 요구사항

- Python 3.10 이상
- Bluetooth 지원 호스트 (라즈베리파이, 노트북 등)
- Linux의 경우 BlueZ 및 D-Bus 필요

---

## 🚀 설치 및 실행

### Linux / macOS

```bash
cd cart_broker
chmod +x run.sh
./run.sh
```

### Windows

```powershell
cd cart_broker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

---

## ⚙️ 환경변수 설정

`.env` 파일을 생성하고 아래 항목을 설정하세요:

```env
# MQTT 브로커 접속 정보
MQTT_HOST=your-mqtt-broker-ip
MQTT_PORT=1883
MQTT_ID=your-mqtt-username
MQTT_PW=your-mqtt-password
MQTT_TOPIC=cart/1
```

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `MQTT_HOST` | MQTT 브로커 호스트 주소 | (필수) |
| `MQTT_PORT` | MQTT 브로커 포트 | `1883` |
| `MQTT_ID` | MQTT 인증 사용자명 | (필수) |
| `MQTT_PW` | MQTT 인증 비밀번호 | (필수) |
| `MQTT_TOPIC` | 발행할 MQTT 토픽 | (필수) |

---

## 📂 프로젝트 구조

```
cart_broker/
├── app.py                 # 메인 진입점
├── requirements.txt       # Python 의존성
├── run.sh                 # 실행 스크립트 (Linux/Mac)
├── .env                   # 환경변수 (gitignore됨)
└── core/
    ├── __init__.py
    ├── config.py          # 설정값 관리
    ├── ble_scanner.py     # BLE 디바이스 스캔
    ├── ble_session.py     # BLE 연결 세션 관리
    ├── uid_tracker.py     # UID 추적 및 만료 처리
    └── mqtt_client.py     # MQTT 연결 및 발행
```

---

## 🔧 동작 원리

1. **BLE 스캔**: 설정된 `service_uuid`로 ESP32 디바이스 탐색
2. **BLE 연결**: 발견된 디바이스에 연결하고 Notify 구독
3. **UID 수신**: ESP32에서 RFID 태그 UID 데이터 수신
4. **TTL 추적**: 5초간 감지되지 않은 UID는 자동 만료
5. **MQTT 발행**: UID 추가/삭제 시 MQTT 토픽으로 현재 UID 목록 발행

---

## 📨 메시지 형식

### ESP32 → cart_broker (BLE Notify)

```
R{리더번호},{UID길이},{16진수UID}
```

**예시**: `R1,4,A1B2C3D4` → 리더 1번에서 UID `A1:B2:C3:D4` 감지

### cart_broker → MQTT Broker

```json
{
  "uids": ["A1:B2:C3:D4", "E5:F6:G7:H8"],
  "time": "2026-01-27 16:30:00"
}
```

---

## 🔌 BLE 설정값

`core/config.py`에서 ESP32 BLE UUID를 확인하세요:

| 설정 | 값 | 설명 |
|------|-----|------|
| `service_uuid` | `7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a01` | ESP32 BLE 서비스 UUID |
| `char_uuid` | `7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a02` | RFID 데이터 특성 UUID |
| `uid_ttl_sec` | `5.0` | 태그 만료 시간 (초) |
| `expiry_check_sec` | `0.5` | 만료 체크 주기 (초) |

---

## 📝 라이선스

이 프로젝트는 S14P11A401 팀 프로젝트의 일부입니다.
