# Smart Shopping Cart

사용자를 따라가는 자율주행 쇼핑카트. RFID로 상품을 자동 인식하고, AI 기반 검색·길안내까지 제공하는 풀스택 시스템.

SSAFY 14기 공통 프로젝트 (2026.01.20 ~ 2026.02.10)

---

## 개요

마트에서 사용자가 카트를 직접 끌지 않아도 되도록, 카트가 사용자를 따라다니며 바구니 안의 RFID 상품을 자동으로 스캔·집계합니다. 모바일 웹에서 상품을 자연어로 검색하면 매장 내 위치까지 안내하고, 결제 단계에서는 카트가 인식한 품목 리스트를 그대로 활용합니다.

---

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 백엔드 | .NET 10, Entity Framework Core 10, MQTTnet 5, Npgsql + Pgvector |
| 프론트엔드 | Next.js 16 (React 19), TypeScript 5, Three.js, Tailwind CSS 4 |
| 임베디드 — 카트 제어 | STM32F103RB (Nucleo, STM32CubeIDE), C |
| 임베디드 — RFID 바구니 | ESP32 + MFRC522 ×4 (PlatformIO/Arduino), NimBLE |
| 임베디드 — 게이트웨이 | Raspberry Pi 5, Python 3.10+ (bleak, paho-mqtt, aiohttp) |
| 데이터 | PostgreSQL + PostGIS + pgvector |
| 메시징 | Eclipse Mosquitto (MQTT) |
| 인프라 / CI | Docker Compose, Jenkins |

---

## 시스템 구조

```
[ESP32 RFID 바구니] ──BLE──▶ [Raspberry Pi 5 게이트웨이] ──MQTT──▶ [.NET 백엔드]
                                                                     │
[STM32 카트 제어부] ◀─UART── (RPi5 동거)                              │
                                                                     ▼
                                                             [PostgreSQL + pgvector]
                                                                     ▲
                                                                     │ REST/SSE
                                                              [Next.js 모바일 웹]
```

- **상품 인식 경로**: ESP32가 4개 RC522 리더로 바구니 내 RFID 태그를 동시 감지 → BLE로 RPi5 게이트웨이에 전송 → MQTT 토픽 `cart/{id}` 로 백엔드에 발행 → PostgreSQL에 카트 상태 갱신.
- **자율주행 경로**: STM32가 모터(TIM3_CH1) / 조향 서보(TIM4_CH1) PWM을 제어. 사용자 추종 명령은 RPi5에서 UART로 전달.
- **AI 검색 경로**: 사용자 자연어 쿼리를 OpenAI 임베딩(`text-embedding-3-small`, SSAFY GMS Proxy 경유)으로 벡터화 → pgvector로 상품 유사도 검색.
- **길안내 경로**: 검색 결과 상품의 매대 좌표를 PostGIS 공간 쿼리로 조회 → 카트의 현재 위치에서 경로 계산 → MQTT `cart/{id}/navigate` 로 카트에 송신.

---

## 주요 기능

- 사용자 추종 자율주행 (PWM 기반 모터·조향 제어)
- RFID 4채널 동시 인식, 200ms 주기 중복 제거 처리
- 자연어 상품 검색 (RAG 임베딩 + pgvector 유사도)
- 매장 내 길안내 (PostGIS 공간 데이터)
- 모바일 웹 장바구니 / 검색 / 길안내 UI (Three.js 3D 시각화)
- MQTT 토픽 기반 카트 상태 실시간 동기화
- 시계절 컨텍스트 기반 상품 추천 임베딩

---

## 디렉터리 구조

| 경로 | 설명 |
|---|---|
| `smart_shopping_cart_back/` | .NET 백엔드 (MQTT 핸들러, 상품/카트 API, 벡터 검색) |
| `smart_shopping_cart_front/` | Next.js 모바일 웹 (검색·길안내·장바구니 UI) |
| `embedded/esp32/` | RFID 바구니 펌웨어 (PlatformIO) |
| `embedded/stm32/` | 카트 모터·조향 제어 펌웨어 (STM32CubeIDE) |
| `embedded/broker_rpi5/` | RPi5 BLE↔MQTT 게이트웨이 (Python) |
| `exec/` | 포팅 매뉴얼, DB 덤프, 시연 시나리오 |
| `Jenkinsfile.back` / `Jenkinsfile.front` | Docker 빌드·배포 파이프라인 |

---

## 실행 방법

사전 준비: Docker 및 Docker Compose v2.24+, MQTT/DB 접속 정보가 담긴 `.env`.

```bash
# 백엔드 (Postgres + Mosquitto + .NET)
cd smart_shopping_cart_back
docker compose up -d --build

# 프론트엔드
cd ../smart_shopping_cart_front
docker build --build-arg NEXT_PUBLIC_API_URL=<백엔드_주소> -t shopping-cart-front .
docker run -d -p 3000:3000 shopping-cart-front
```

임베디드 측은 STM32CubeIDE / PlatformIO에서 각각 펌웨어를 플래시하고, RPi5에는 `embedded/broker_rpi5` 디렉터리의 Python 앱을 실행합니다. 자세한 환경 변수와 핀 매핑은 `exec/Porting_Manual.md` 참조.

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
