# Smart Shopping Cart

사용자를 따라가는 자율주행 RC 카트, RFID 자동 인식 바구니, AI 기반 검색·길안내 모바일 웹을 통합한 풀스택 스마트 쇼핑 시스템.

SSAFY 14기 공통 프로젝트 (2026.01.20 ~ 2026.02.10)

---

## 개요

마트에서 사용자가 카트를 직접 끌지 않아도 되는 환경을 목표로 다음 4개 서브시스템을 통합 구현했습니다.

- **자율주행 RC 카트** — 카메라 + LiDAR 센서 퓨전으로 사용자 인식·추적, SLAM 기반 매장 내 자율 이동
- **RFID 바구니** — ESP32 4채널 RFID 리더로 담긴 상품을 자동 스캔, BLE → MQTT로 백엔드에 전송
- **백엔드** — .NET 10 + PostgreSQL + pgvector 기반, MQTT 메시지 처리와 AI 임베딩 상품 검색
- **모바일 웹** — 자연어 상품 검색, 매장 길안내, 장바구니 실시간 동기화

---

## 기술 스택

### 카트 추적·자율주행

| 영역 | 사용 기술 |
|---|---|
| 인식·추적 | Python, ROS2, YOLO, DeepSORT, OpenCV |
| 거리 측정 | YDLidar 2D LiDAR (6Hz) |
| 자율주행 | Cartographer SLAM, Nav2 |
| 컴퓨팅 | Jetson Orin Nano |
| 모터 제어 | STM32F103RB, UART 시리얼 |
| 영상 전송 | ZMQ |

### 쇼핑 시스템

| 영역 | 사용 기술 |
|---|---|
| RFID 바구니 | ESP32 + MFRC522 ×4, PlatformIO, NimBLE |
| 게이트웨이 | Raspberry Pi 5, Python (bleak, paho-mqtt, aiohttp) |
| 백엔드 | .NET 10, EF Core 10, MQTTnet 5, Pgvector |
| 프론트엔드 | Next.js 16 (React 19), TypeScript 5, Three.js, Tailwind CSS 4 |
| 데이터 | PostgreSQL + PostGIS + pgvector |
| 메시징 | Eclipse Mosquitto (MQTT) |
| 인프라·CI | Docker Compose, Jenkins |

---

## 시스템 구조

```
                        [사용자]
                           │
            ┌──────────────┴──────────────┐
            │                             │
   카메라/LiDAR로 추적                상품 담기
            │                             │
            ▼                             ▼
    ┌──────────────┐              ┌──────────────┐
    │  RC 카트     │              │ RFID 바구니  │
    │  (Jetson)    │              │  (ESP32)     │
    │  YOLO+       │              │  MFRC522 ×4  │
    │  DeepSORT    │              └──────┬───────┘
    │  +LiDAR Fuse │                     │ BLE
    │  → STM32     │                     ▼
    └──────────────┘              ┌──────────────┐
                                  │ Raspberry Pi 5│
                                  │  BLE→MQTT    │
                                  └──────┬───────┘
                                         │ MQTT
                                         ▼
                                  ┌──────────────┐
                                  │ .NET 백엔드  │
                                  │ + Postgres   │
                                  │   pgvector   │
                                  └──────┬───────┘
                                         │ REST/SSE
                                         ▼
                                  ┌──────────────┐
                                  │ 모바일 웹    │
                                  │ (Next.js)    │
                                  └──────────────┘
```

### 카트 추적 경로 (rc_tracking)

1. Jetson Orin Nano 카메라(30fps)에서 YOLO로 사용자 검출, DeepSORT로 다중 ID 추적
2. YDLidar(6Hz)에서 2D 거리 스캔
3. **센서 퓨전** — 카메라 픽셀 좌표를 LiDAR 각도 좌표로 직접 변환 (FOV 55.3° 기반), 오프셋 캘리브레이션과 인접 각도 평균 필터링 적용
4. **주기 불일치 해결** — 30Hz 카메라 vs 6Hz LiDAR 동기화 대신, LiDAR 최신 스캔을 캐싱하고 카메라 검출 시점에 비동기 참조 (`scan_lock` 멀티스레드)
5. 사용자 거리·각도 → STM32에 UART 시리얼(`/dev/ttyACM0`) 명령 송신 (`x` 조향, `z` 전진, `r` 후진), PWM 모터·서보 구동
6. 능동 브레이크(후진 펄스) 로직으로 관성 충돌 방지, 색상 히스토그램 기반 Re-ID로 ID 스위칭 빠른 복구

### 자율주행·길안내 경로 (slam_mapping)

- Cartographer SLAM으로 매장 사전 매핑 후 Nav2 기반 경로 계획
- FOLLOW(사용자 추적) ↔ NAVIGATE(자율주행 길안내) 듀얼 모드

### 상품 인식 경로 (embedded → backend)

1. ESP32가 4개 MFRC522 리더로 바구니 내 RFID 태그 동시 감지, 200ms 중복 제거
2. BLE로 RPi5 게이트웨이에 전송 → MQTT 토픽 `cart/{id}` 로 백엔드 발행
3. .NET 백엔드의 `MqttHostedService`가 PostgreSQL에 카트 상태 갱신

### AI 검색·길안내 경로

- 자연어 쿼리 → OpenAI 임베딩(`text-embedding-3-small`, SSAFY GMS Proxy 경유) → pgvector 유사도 검색
- 검색된 상품의 매대 좌표 → PostGIS 공간 쿼리 → Nav2 경로 계산 → MQTT `cart/{id}/navigate` 송신

---

## 주요 기능

- 사용자 추종 자율주행 (카메라+LiDAR 센서 퓨전, 30fps × 6Hz 비동기 캐싱 설계)
- 매장 내 SLAM 기반 자율 길안내 (Cartographer + Nav2)
- RFID 4채널 동시 인식, 200ms 중복 제거
- 자연어 상품 검색 (RAG 임베딩 + pgvector 유사도)
- 매장 길안내 (PostGIS 공간 데이터)
- 모바일 웹 장바구니·검색·길안내 UI (Three.js 3D 시각화)
- MQTT 토픽 기반 카트 상태 실시간 동기화
- 시계절 컨텍스트 기반 상품 추천 임베딩

---

## 디렉터리 구조

| 경로 | 설명 |
|---|---|
| `rc_tracking/` | RC 카트 ROS2 워크스페이스 — YOLO/DeepSORT 추적, LiDAR 센서 퓨전, STM32 모터 제어 |
| `slam_mapping/` | Cartographer SLAM + Nav2 자율주행 워크스페이스 |
| `embedded/esp32/` | RFID 바구니 펌웨어 (PlatformIO) |
| `embedded/stm32/` | STM32 펌웨어 (UART 모터 제어) |
| `embedded/broker_rpi5/` | RPi5 BLE ↔ MQTT 게이트웨이 (Python) |
| `smart_shopping_cart_back/` | .NET 백엔드 (MQTT 핸들러, 상품/카트 API, 벡터 검색) |
| `smart_shopping_cart_front/` | Next.js 모바일 웹 (검색·길안내·장바구니 UI) |
| `exec/` | 포팅 매뉴얼, DB 덤프, 시연 시나리오 |
| `Jenkinsfile.back` / `Jenkinsfile.front` | Docker 빌드·배포 파이프라인 |

---

## 실행 방법

사전 준비: Docker 및 Docker Compose v2.24+, ROS2 Humble, Jetson Orin Nano (혹은 PC), MQTT/DB 접속 정보가 담긴 `.env`.

```bash
# 백엔드 (Postgres + Mosquitto + .NET)
cd smart_shopping_cart_back
docker compose up -d --build

# 프론트엔드
cd ../smart_shopping_cart_front
docker build --build-arg NEXT_PUBLIC_API_URL=<백엔드_주소> -t shopping-cart-front .
docker run -d -p 3000:3000 shopping-cart-front

# RC 카트 추적 노드 (Jetson)
cd ../rc_tracking
colcon build && source install/setup.bash
ros2 launch rc_detection tracking_system.launch.py

# SLAM 매핑 / 자율주행
cd ../slam_mapping
colcon build && source install/setup.bash
ros2 launch <slam_or_nav2_launch_file>
```

임베디드 펌웨어는 PlatformIO(ESP32) / STM32CubeIDE(STM32)로 각각 플래시하고, RPi5에는 `embedded/broker_rpi5` 디렉터리의 Python 앱을 실행합니다. 자세한 환경 변수와 핀 매핑은 `exec/Porting_Manual.md` 참조.

---

## 커밋 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/) 형식: `type(scope): subject [Jira-ID]`

| Type | 설명 |
|---|---|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `style` | 코드 포맷팅 |
| `refactor` | 리팩터링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드/패키지 등 기타 |
| `perf` | 성능 개선 |
| `ci` | CI/CD 설정 |
