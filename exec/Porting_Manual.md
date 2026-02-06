# Porting Manual (포팅 매뉴얼)

## 1. 개요 (Overview)
본 문서는 **S14P11A401 (Smart Shopping Cart)** 프로젝트의 빌드, 배포 및 환경 설정을 위한 가이드입니다.

## 2. 시스템 환경 (System Environment)

### 2.1 서버 정보 (Server Info)
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: 6.14.0-1018-aws
- **CPU Arch**: x86_64
- **RAM**: 15GB

### 2.2 사용 소프트웨어 및 버전 (Software Versions)
| 구분 | 항목 | 버전 / 이미지 | 비고 |
|------|------|---------------|------|
| **Backend** | Framework | .NET Core | Dockerfile 기준 `sdk:10.0` (확인 필요, 통상 8.0/9.0 사용) |
| **Frontend** | Framework | Next.js (Node.js 20) | `node:20-alpine` |
| **Database** | RDBMS | PostgreSQL + PostGIS | `smart-cart-db` 컨테이너 |
| **Message Broker** | MQTT | Eclipse Mosquitto | `latest` |
| **Infra** | Runtime | Docker / Docker Compose | v2.24.1 이상 권장 |

## 3. 빌드 및 배포 가이드 (Build & Deploy)

### 3.1 환경 변수 설정 (Environment Variables)
배포 전 아래 환경 변수들을 `.env` 파일 또는 시스템 환경 변수로 설정해야 합니다.

#### Backend (`smart_shopping_cart_back/.env`)
| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `MQTT_BROKER` | MQTT 브로커 호스트명 | `mqtt-broker` (도커 내부) / `localhost` |
| `MQTT_PORT` | MQTT 포트 | `1883` |
| `MQTT_TOPIC` | 카트 통신 토픽 | `cart/1` |
| `MQTT_USERNAME` | MQTT 접속 계정 | `CartLidar` |
| `MQTT_PASSWORD` | MQTT 접속 암호 | `***REDACTED-MQTT-PW***` |
| `DB_USER` | DB 사용자명 | `myuser` |
| `DB_PASSWORD` | DB 비밀번호 | `my-secure-password-123` |
| `DB_NAME` | DB 데이터베이스명 | `smart_cart` |
| `GMS_KEY` | SSAFY GMS API 키 | `S14P12A401...` |

#### Frontend (`smart_shopping_cart_front/.env` / `Dockerfile` ARG)
| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API 주소 | `https://i14a401.p.ssafy.io` |

### 3.2 배포 순서 (Deployment Steps)

1. **소스 클론**:
   ```bash
   git clone [Repository URL] S14P11A401
   cd S14P11A401
   ```

2. **Backend 배포**:
   ```bash
   cd smart_shopping_cart_back
   # .env 파일 생성 (위 환경변수 참조)
   docker-compose up -d --build
   ```

3. **Frontend 배포**:
   ```bash
   cd ../smart_shopping_cart_front
   # Docker 이미지 빌드 및 실행
   docker build --build-arg NEXT_PUBLIC_API_URL=https://... -t smart-cart-frontend .
   docker run -d -p 8002:3000 --name smart-cart-frontend smart-cart-frontend
   ```

4. **Infra (MQTT) 배포**:
   ```bash
   cd ../infra
   docker-compose up -d
   ```

### 3.3 배포 시 특이사항
- **MQTT**: `infra` 폴더의 mosquitto 컨테이너가 먼저 실행되어 있어야 백엔드가 정상적으로 MQTT 브로커에 연결됩니다.
- **DB Init**: 백엔드 최초 실행 시 `db/init` 폴더의 SQL 스크립트들이 자동으로 실행되어 테이블 및 초기 데이터(벡터 데이터 포함)가 생성됩니다.
- **Port**:
  - Backend API: `8123` (External) -> `5000` (Internal)
  - Frontend: `8002` (External) -> `3000` (Internal)
  - MQTT: `8883` (External/SSL) -> `1883` (Internal)

## 4. 데이터베이스 접속 정보 (DB Connection)

## 5. 임베디드 포팅 가이드 (Embedded / STM32F103RB)

본 섹션은 **S14P11A401 (Smart Shopping Cart)** 프로젝트의 카트 구동부(조향/구동) 제어를 담당하는 **STM32F103RB** 펌웨어 포팅(빌드/업로드/연결) 가이드입니다.

---

### 5.1 하드웨어 구성 (Hardware)

- **MCU 보드**: STM32F103RB (예: Nucleo-F103RB)
- **모터 드라이버**: L298N (현재 사용)
- **구동 모터**: DC Motor (RC 카 구동)
- **조향**: Servo Motor

#### 5.1.1 기본 배선 (Wiring)
> 아래 핀은 현재 펌웨어 기준 예시이며, `.ioc` 설정과 일치해야 합니다.

- **모터 PWM**
  - `PA6` : `TIM3_CH1` → L298N `ENA(PWM)`
- **모터 방향**
  - `PA10` → L298N `IN1`
  - `PB4`  → L298N `IN2`
- **서보 PWM**
  - `PB6` : `TIM4_CH1` → Servo Signal
- **UART 통신 (Jetson/RPi ↔ STM32)**
  - `USART2` 사용 (보드 설정에 따라 ST-LINK VCP 또는 외부 USB-UART 사용)
- **전원**
  - 모터 전원(배터리팩 5V)은 **L298N에 공급**
  - STM32 전원은 USB(ST-LINK) 또는 별도 5V/3.3V
  - **GND는 반드시 공통**: STM32 GND = L298N GND = 배터리 GND

---

### 5.2 펌웨어 프로젝트 위치 (Repository Path)

- 브랜치: `stm32`
- 경로: `stm/a401_stm32_control/`
  - `ppl.ioc` : STM32CubeMX 설정 파일
  - `Core/Src/`, `Core/Inc/` : 애플리케이션 및 드라이버 코드

---

### 5.3 개발/빌드 환경 (Build Environment)

- **IDE**: STM32CubeIDE (Windows 권장)
- **Programmer/Debugger**: ST-LINK (Nucleo 내장 ST-LINK 사용 가능)
- **툴체인**: arm-none-eabi-gcc (CubeIDE 내장)

---

### 5.4 빌드 및 업로드 절차 (Build & Flash)

1) **레포 클론 및 브랜치 이동**
```bash
git clone [Repository URL] S14P11A401
cd S14P11A401
git switch stm32
 - **Host**: `localhost` (외부) 또는 `db` (도커 내부 네트워크 `cart-network`)
 - **Port**: `5432`
 - **Database**: `smart_cart`
 - **User**: `myuser`
 - **Password**: `my-secure-password-123`

## 6. ESP32 카트 바구니 (cart_basket) 포팅 가이드

본 섹션은 **카트 바구니 RFID 인식(ESP32 + RC522)** 펌웨어의 빌드/업로드/연결 방법을 설명합니다.

---

### 6.1 펌웨어 위치 (Repository Path)

- 경로: `cart_basket/`
  - `platformio.ini`
  - `src/main.cpp`

---

### 6.2 개발/빌드 환경 (Build Environment)

- **보드**: ESP32 DevKit (board: `esp32dev`)
- **프레임워크**: Arduino (Arduino IDE)
- **시리얼 속도**: `115200`
- **라이브러리**
  - `miguelbalboa/MFRC522`
  - `h2zero/NimBLE-Arduino`

---

### 6.3 하드웨어 구성 (Hardware)

- **RFID 리더**: RC522 * 4개
- **SPI 핀 (ESP32)**
  - `SCK`: `GPIO18`
  - `MISO`: `GPIO19`
  - `MOSI`: `GPIO23`
- **RC522 CS 핀 (SS)**
  - Reader1: `GPIO5`
  - Reader2: `GPIO17`
  - Reader3: `GPIO16`
  - Reader4: `GPIO27`
- **RC522 RST (공용)**: `GPIO22`
- **전원**
  - RC522: 3.3V 사용 권장
  - GND 공통

---

### 6.4 BLE 프로파일 (BLE GATT)

- **Device Name**: `RC522-GATT`
- **Service UUID**: `7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a01`
- **Characteristic UUID**: `7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a02`
- **전송 형식 (Notify Payload)**  
  `R<readerId>,<uidLen>,<UID_HEX>`  
  예: `R1,4,DEADBEEF`

---

### 6.5 빌드 및 업로드 절차 (Arduino IDE)

1. **스케치 로드**
   - `cart_basket/src/main.cpp`를 Arduino IDE로 엽니다.

2. **보드/포트 설정**
   - 보드: `ESP32 Dev Module` (또는 사용 보드에 맞게 선택)
   - 포트: 연결된 ESP32 시리얼 포트 선택

3. **라이브러리 설치**
   - `MFRC522` (by miguelbalboa)
   - `NimBLE-Arduino` (by h2zero)

4. **빌드 및 업로드**
   - Arduino IDE에서 업로드(Upload)

5. **시리얼 모니터**
   - 속도 `115200`으로 설정

---

### 6.6 동작 확인 체크리스트

- ESP32 부팅 후 시리얼에 `scan start` 로그 출력
- BLE 광고 `RC522-GATT` 확인
- 중앙 장치가 연결되면 Notify 수신
- 동일 UID는 `REPEAT_MS = 200ms` 주기로 반복 전송
